// Theme colours come from the CSS custom properties, so the figures follow light and dark mode.
function hex2rgb(h){h=h.trim().replace('#','');if(h.length===3)h=h.split('').map(function(c){return c+c}).join('');var n=parseInt(h,16);return[n>>16&255,n>>8&255,n&255]}
function themeColors(){
  var cs=getComputedStyle(document.documentElement),o={};
  ['paper','ink','acc','mute','rule'].forEach(function(k){var hx=cs.getPropertyValue('--'+(k==='acc'?'fig':k)).trim(),c=hex2rgb(hx);o[k]=c;o[k+'R']=c.join(',');o[k+'Hex']=hx});
  return o;
}
var C=themeColors();
document.addEventListener('themechange',function(){C=themeColors()});
function mix(a,b,t){return[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]}
function clamp(v,a,b){return v<a?a:v>b?b:v}
function smooth(a,b,x){var t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t)}
function fitCanvas(c,ctx,w,h,maxPx){
  var d=Math.max(1,Math.min(devicePixelRatio||1,Math.sqrt(maxPx/Math.max(1,w*h))));   // cap the pixel count
  c.width=Math.round(w*d);c.height=Math.round(h*d);ctx.setTransform(d,0,0,d,0,0);return d;
}
function placeTip(tip,box,x,y){
  tip.style.display='block';
  var w=tip.offsetWidth,h=tip.offsetHeight,bw=box.clientWidth,bh=box.clientHeight;
  var l=x+16,t=y+16;if(l+w>bw-8)l=x-w-16;if(t+h>bh-8)t=y-h-16;
  tip.style.left=Math.max(8,l)+'px';tip.style.top=Math.max(8,t)+'px';
}

// ================================================================ Hero: a live mel spectrogram
// It scrolls the way a real speech analyser does. The speech is synthesised on the fly: voiced
// vowels (a harmonic comb under moving formants), fricative noise, stop closures and bursts,
// nasals, and pauses between phrases. The cursor works as a listener: it reads out the frequency
// and names what is under it. Three tags at the right edge follow the live formants.
// Kept cheap: one small canvas that is shifted and extended a column at a time, one overlay for
// the labels, and it sleeps completely when off screen or in a hidden tab.
(function(){
  var viz=document.getElementById('vizA'),spec=document.getElementById('spec'),ov=document.getElementById('ovA'),tip=document.getElementById('tipA');
  if(!viz)return;
  var RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var sx=spec.getContext('2d'),ox=ov.getContext('2d');
  var NB=120,FMAX=8000,CPS=60,SC=2,RING=4096;
  function mel(f){return 2595*Math.log10(1+f/700)}
  function imel(m){return 700*(Math.pow(10,m/2595)-1)}
  var MM=mel(FMAX),FREQ=new Float32Array(NB);for(var i=0;i<NB;i++)FREQ[i]=imel(i/(NB-1)*MM);

  // colour ramp: from the page colour, through the accent, to the ink, like a printed spectrogram
  var LUT=new Uint8Array(256*3);
  function buildLUT(){
    var stops=[[0].concat(C.paper),[.1].concat(mix(C.paper,C.acc,.05)),[.3].concat(mix(C.paper,C.acc,.3)),[.5].concat(mix(C.paper,C.acc,.8)),[.76].concat(mix(C.acc,C.ink,.45)),[1].concat(C.ink)];
    for(var i=0;i<256;i++){var v=i/255,k=0;while(k<stops.length-2&&v>stops[k+1][0])k++;var a=stops[k],b=stops[k+1],t=(v-a[0])/(b[0]-a[0]);
      for(var c=0;c<3;c++)LUT[i*3+c]=a[c+1]+(b[c+1]-a[c+1])*t}
  }
  buildLUT();

  // ---- speech synthesiser ----
  var VOW={a:[730,1090,2440],e:[530,1840,2480],i:[270,2290,3010],o:[570,840,2410],u:[300,870,2240],x:[660,1720,2410]},VK=Object.keys(VOW);
  var queue=[],cur=null,curT=0,segId=0,segs={};
  var S={F:[500,1500,2500],Ft:[500,1500,2500],f0:125,v:0,vT:0,nz:0,nzT:0,lo:3000,hi:7600,phrase:0,phraseTot:1};
  var TYPE={pause:0,vowel:1,fric:2,burst:3,nasal:4,stop:5,asp:6};
  function pushPhrase(){
    var n=3+Math.floor(Math.random()*4);
    for(var s=0;s<n;s++){
      var r=Math.random();
      if(r<.20){queue.push({type:'stop',dur:.06+.03*Math.random()});queue.push({type:'burst',dur:.014});queue.push({type:'asp',dur:.03})}
      else if(r<.42)queue.push({type:'fric',dur:.09+.07*Math.random(),lo:3000+Math.random()*1500,hi:7700});
      else if(r<.56)queue.push({type:'nasal',dur:.07+.04*Math.random()});
      queue.push({type:'vowel',v:VK[Math.floor(Math.random()*VK.length)],dur:.15+.13*Math.random(),acc:Math.random()<.35});
      if(Math.random()<.2)queue.push({type:'nasal',dur:.06});
    }
    queue.push({type:'pause',dur:.28+.42*Math.random()});
    var tot=0;for(var q=0;q<queue.length;q++)tot+=queue[q].dur;S.phrase=0;S.phraseTot=tot;
  }
  function stepSynth(dt){
    if(!cur||curT>=cur.dur){
      if(!queue.length)pushPhrase();
      cur=queue.shift();curT=0;cur.id=++segId;segs[cur.id]=cur;delete segs[cur.id-400];
    }
    curT+=dt;S.phrase+=dt;
    switch(cur.type){
      case 'vowel':S.Ft=VOW[cur.v];S.vT=cur.acc?1:.78;S.nzT=0;break;
      case 'fric':S.vT=0;S.nzT=.55;S.lo=cur.lo;S.hi=cur.hi;break;
      case 'burst':S.vT=0;S.nzT=.62;S.lo=1800;S.hi=6200;break;
      case 'asp':S.vT=0;S.nzT=.2;S.lo=1200;S.hi=5200;break;
      case 'nasal':S.vT=.42;S.nzT=0;S.Ft=[260,1250,2500];break;
      default:S.vT=0;S.nzT=0;
    }
    var kf=1-Math.exp(-dt/.04);for(var k=0;k<3;k++)S.F[k]+=(S.Ft[k]-S.F[k])*kf;
    S.v+=(S.vT-S.v)*(1-Math.exp(-dt/(S.vT>S.v?.02:.05)));
    S.nz+=(S.nzT-S.nz)*(1-Math.exp(-dt/.012));
    var p=Math.min(1,S.phrase/S.phraseTot);
    S.f0=128*(1-.22*p)*(1+(cur.acc?.08:0))*(1+.012*Math.sin(S.phrase*7));
  }

  // ---- column history ----
  var H1=new Float32Array(RING),H2=new Float32Array(RING),H3=new Float32Array(RING),H0=new Float32Array(RING),HV=new Float32Array(RING);
  var HK=new Uint8Array(RING),HS=new Int32Array(RING),col=0,colBuf=new Uint8Array(NB);
  var BW=[95,130,190];
  function makeColumn(){
    stepSynth(1/CPS);
    var F=S.F,v=S.v,nz=S.nz,f0=S.f0,lo=S.lo,hi=S.hi,idx=col%RING;
    for(var i=0;i<NB;i++){
      var f=FREQ[i],I=0;
      if(v>.01){
        var env=.16*Math.exp(-f/2600);
        for(var k=0;k<3;k++){var d=(f-F[k])/BW[k];env+=(k===0?1:k===1?.82:.55)*Math.exp(-d*d)}
        var cm=Math.cos(6.2831853*f/f0),peak=cm>0?Math.pow(cm,6):0,ct=clamp(1.1-f/3200,.12,1);
        I+=v*env*(.22+.78*(ct*peak+(1-ct)*.45));
      }
      if(nz>.01){
        var band=smooth(lo*.8,lo,f)*(1-smooth(hi,hi*1.1,f));
        I+=nz*band*(.5+.5*Math.random());
      }
      I=I*.92+.018*Math.random();
      colBuf[i]=Math.pow(clamp(I,0,1),.62)*255|0;
    }
    H1[idx]=F[0];H2[idx]=F[1];H3[idx]=F[2];H0[idx]=f0;HV[idx]=v;HK[idx]=TYPE[cur.type];HS[idx]=cur.id;
    col++;
  }
  var BW_=0,W=0,H=0,lastW=0,acc=0,last=0,raf=0,running=false,vis=true,px=-1,py=-1;
  function pushColumns(n){
    var img=sx.createImageData(n,NB),pd=img.data;
    for(var c=0;c<n;c++){
      makeColumn();
      for(var i=0;i<NB;i++){var y=NB-1-i,o=(y*n+c)*4,l=colBuf[i]*3;pd[o]=LUT[l];pd[o+1]=LUT[l+1];pd[o+2]=LUT[l+2];pd[o+3]=255}
    }
    if(n<BW_)sx.drawImage(spec,n,0,BW_-n,NB,0,0,BW_-n,NB);
    sx.putImageData(img,BW_-n,0);
  }

  // ---- labels drawn over the spectrogram ----
  function yOf(f){return H*(1-mel(f)/MM)}
  function xOfCol(c){return W-(col-1-c)*SC}
  function fmtHz(f){return f>=1000?(f/1000).toFixed(f>=10000?0:2).replace(/\.?0+$/,'')+' kHz':Math.round(f)+' Hz'}
  var AX=[250,500,1000,2000,4000,8000];   // 100 Hz is left out: it would sit on top of the time axis
  function drawOverlay(){
    if(!W)return;
    ox.clearRect(0,0,W,H);
    ox.font='500 11px "Albert Sans",sans-serif';ox.textBaseline='middle';
    var padL=Math.max(16,(W-1180)/2+Math.min(64,W*.05)),axX=W>700?22:12;   // legend lines up with the page column; the frequency axis sits at the left edge
    for(var k=0;k<AX.length;k++){                                     // frequency axis
      var y=yOf(AX[k]);if(y<14||y>H-10)continue;
      ox.strokeStyle='rgba('+C.inkR+',.10)';ox.beginPath();ox.moveTo(0,y);ox.lineTo(W,y);ox.stroke();
      ox.textAlign='left';var lab=fmtHz(AX[k]),tw=ox.measureText(lab).width;
      ox.fillStyle='rgba('+C.paperR+',.62)';ox.fillRect(axX-5,y-8,tw+10,16);
      ox.fillStyle='rgba('+C.inkR+',.55)';ox.fillText(lab,axX,y);
    }
    ox.textAlign='center';                                            // time axis: a tick every second
    var c0=col-1-Math.floor(W/SC);c0=c0-(c0%CPS);
    for(var c=c0;c<col;c+=CPS){
      if(c<0)continue;var x=xOfCol(c);if(x<92||x>W-40)continue;
      ox.strokeStyle='rgba('+C.inkR+',.18)';ox.beginPath();ox.moveTo(x,H-14);ox.lineTo(x,H-6);ox.stroke();
      ox.fillStyle='rgba('+C.inkR+',.4)';ox.fillText('-'+Math.round((col-1-c)/CPS)+' s',x,H-20);
    }
    var firstCol=Math.max(0,col-Math.floor(W/SC)),run=-1;            // pause brackets
    for(var c=firstCol;c<=col;c++){
      var idx=c%RING,isP=c<col&&HK[idx]===0&&segs[HS[idx]]&&segs[HS[idx]].type==='pause';
      if(isP&&run<0)run=c;
      if((!isP||c===col)&&run>=0){
        var dur=(c-run)/CPS,x1=xOfCol(run),x2=xOfCol(c-1);
        if(dur>=.24&&x2-x1>30&&x1>110&&x2<W-30){
          var yb=H-34;ox.strokeStyle='rgba('+C.accR+',.55)';ox.beginPath();ox.moveTo(x1,yb-4);ox.lineTo(x1,yb);ox.lineTo(x2,yb);ox.lineTo(x2,yb-4);ox.stroke();
          ox.fillStyle='rgba('+C.accR+',.85)';ox.fillText('pause '+Math.round(dur*1000)+' ms',(x1+x2)/2,yb-12);
        }
        run=-1;
      }
    }
    var li=(col-1)%RING,vv=clamp(HV[li]*1.3,0,1);                     // live formant tags
    if(vv>.08){
      ox.textAlign='right';var F=[H1[li],H2[li],H3[li]];
      for(var k=0;k<3;k++){
        var y=yOf(F[k]),a=vv*(k===0?1:.85);
        ox.fillStyle='rgba('+C.accR+','+a.toFixed(2)+')';ox.beginPath();ox.arc(W-8,y,2.4,0,6.283);ox.fill();
        var lab='F'+(k+1)+'  '+Math.round(F[k]),tw=ox.measureText(lab).width;
        ox.fillStyle='rgba('+C.paperR+','+(a*.6).toFixed(2)+')';ox.fillRect(W-20-tw-4,y-8,tw+8,16);
        ox.fillStyle='rgba('+C.inkR+','+(a*.9).toFixed(2)+')';ox.fillText(lab,W-20,y);
      }
    }
    if(px>=0&&px<=W&&py>=0&&py<=H){                                   // the listener
      ox.strokeStyle='rgba('+C.accR+',.7)';ox.beginPath();ox.moveTo(px,0);ox.lineTo(px,H);ox.moveTo(0,py);ox.lineTo(W,py);ox.stroke();
      readout();
    }else tip.style.display='none';
  }
  function readout(){
    var c=col-1-Math.round((W-px)/SC);if(c<0||c>=col){tip.style.display='none';return}
    var idx=c%RING,f=imel((1-py/H)*MM),kind=HK[idx],seg=segs[HS[idx]],ago=((col-1-c)/CPS).toFixed(1),what='';
    if(kind===1||kind===4){
      var F=[H1[idx],H2[idx],H3[idx]],hit=-1;
      for(var k=0;k<3;k++)if(Math.abs(f-F[k])<F[k]*.13)hit=k;
      if(hit>=0)what='<i>F'+(hit+1)+'</i> formant, <em>'+Math.round(F[hit])+' Hz</em>';
      else if(f<H0[idx]*1.5)what='<i>pitch</i> (f0), <em>'+Math.round(H0[idx])+' Hz</em>';
      else what='<i>harmonic '+Math.max(2,Math.round(f/H0[idx]))+'</i> of '+Math.round(H0[idx])+' Hz';
      what=(kind===4?'nasal · ':'vowel · ')+what;
    }else if(kind===2)what='<i>fricative</i> noise';
    else if(kind===3||kind===6)what='<i>stop burst</i>';
    else if(kind===5)what='<i>stop closure</i> (silence)';
    else what='<i>pause</i>'+(seg?', '+Math.round(seg.dur*1000)+' ms':'');
    tip.innerHTML='<b>'+fmtHz(f)+' · '+ago+' s ago</b>'+what;
    placeTip(tip,viz,px,py);
  }

  // ---- sizing: a new buffer only when the width changes, so a phone's collapsing address bar never resets it ----
  function layout(force){
    var w=viz.clientWidth,h=viz.clientHeight;if(!w||!h)return;
    W=w;H=h;
    if(force||w!==lastW){
      lastW=w;BW_=Math.max(120,Math.round(W/SC));spec.width=BW_;spec.height=NB;
      sx.fillStyle=C.paperHex;sx.fillRect(0,0,BW_,NB);
      var rest=BW_;while(rest>0){var n=Math.min(rest,64);pushColumns(n);rest-=n}   // pre-roll so it is full from the first frame
    }
    fitCanvas(ov,ox,W,H,2.2e6);
    drawOverlay();
  }
  function frame(ts){
    if(!running)return;
    var dt=Math.min((ts-last)/1000,.1);last=ts;acc+=dt*CPS;
    var n=Math.floor(acc);acc-=n;
    if(n>0){pushColumns(Math.min(n,12))}
    drawOverlay();
    raf=requestAnimationFrame(frame);
  }
  function start(){if(running||RM||document.hidden||!vis)return;running=true;last=performance.now();raf=requestAnimationFrame(frame)}
  function stop(){running=false;cancelAnimationFrame(raf)}
  viz.addEventListener('pointermove',function(e){var r=viz.getBoundingClientRect();px=e.clientX-r.left;py=e.clientY-r.top;if(!running)drawOverlay()},{passive:true});
  viz.addEventListener('pointerleave',function(){px=py=-1;tip.style.display='none';if(!running)drawOverlay()});
  new ResizeObserver(function(){layout(false)}).observe(viz);
  document.addEventListener('themechange',function(){buildLUT();layout(true)});
  layout(true);
  new IntersectionObserver(function(es){vis=es[0].isIntersecting;vis?start():stop()}).observe(viz);   // no work while off screen
  document.addEventListener('visibilitychange',function(){document.hidden?stop():start()});
  start();
})();

// ================================================================ Research: two scorers, one question
// A stream of spoken responses. For each one a human rater gives a score (gold line) and an
// automated scorer gives its own (ivory line). Most of the time they track each other; every so
// often the machine departs from the human for a few responses. The dashed cut score decides
// pass or fail, so what matters is not just any gap but a gap that puts the two on opposite sides
// of that line ("decision flips"). An illustration of the question, not study data.
(function(){
  var box=document.getElementById('vizB'),cv=document.getElementById('scope'),tip=document.getElementById('tipB');
  if(!box)return;
  var ctx=cv.getContext('2d'),RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var SPEED=70,DT=.85,CUT=3.5,PT=70,PB=40,PR=104,W=0,H=0,running=false,vis=true,raf=0,px=-1,py=-1,staticNow=performance.now()/1000;
  var S=[],hPrev=3.7,epiLeft=0,epiDev=0,nextEpi=4,seq=0;
  function randn(){var u=0,v=0;while(!u)u=Math.random();while(!v)v=Math.random();return Math.sqrt(-2*Math.log(u))*Math.cos(6.2831853*v)}
  function gen(t){
    hPrev=3.65+.8*(hPrev-3.65)+randn()*.5;hPrev=clamp(hPrev,1.4,5.7);
    if(epiLeft<=0&&--nextEpi<=0){
      epiLeft=2+Math.floor(Math.random()*3);nextEpi=4+Math.floor(Math.random()*5);
      var side=Math.random()<.78?(hPrev>CUT?-1:1):(Math.random()<.5?-1:1);
      epiDev=side*(.9+Math.random()*.7);
    }
    var dev=0;if(epiLeft>0){dev=epiDev*(.75+.25*Math.random());epiLeft--}
    var m=clamp(hPrev+dev+randn()*.16,1,6);
    S.push({t:t,h:hPrev,m:m,flip:(hPrev>=CUT)!==(m>=CUT),id:seq++});
  }
  function fill(now){
    var span=W/SPEED+4*DT;
    if(!S.length){var t=now-span;while(t<=now+3*DT){gen(t);t+=DT}}
    else{var l=S[S.length-1].t;while(l<now+3*DT){l+=DT;gen(l)}}
    while(S.length>6&&S[1].t<now-span)S.shift();
  }
  function cr(p0,p1,p2,p3,t){return .5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)}   // Catmull-Rom
  function at(tau,key){
    var f=(tau-S[0].t)/DT,i=Math.floor(f),t=f-i,n=S.length;
    var g=function(j){return S[clamp(j,0,n-1)][key]};
    return cr(g(i-1),g(i),g(i+1),g(i+2),t);
  }
  function yOf(s){return PT+(6-s)/5*(H-PT-PB)}
  function size(){
    var w=box.clientWidth,h=box.clientHeight;if(!w||!h)return;
    W=w;H=h;PR=W<520?96:118;SPEED=W<520?44:70;fitCanvas(cv,ctx,W,H,2.2e6);S=[];
    if(!running)draw(staticNow);
  }
  var STEP=3;
  function draw(now){
    if(!W||!H)return;
    fill(now);
    ctx.clearRect(0,0,W,H);
    var xR=W-PR,xL=40,padL=xL-30;
    if(xR-xL<80)return;                                               // too narrow to draw (a hidden or tiny container)
    var tauOf=function(x){return now-(xR-x)/SPEED};
    ctx.font='500 11px "Albert Sans",sans-serif';ctx.textBaseline='middle';
    

    ctx.textAlign='left';                                             // grid and score scale
    for(var s=1;s<=6;s++){
      var y=yOf(s);ctx.strokeStyle='rgba('+C.inkR+','+(s===1||s===6?.12:.07)+')';ctx.beginPath();ctx.moveTo(xL,y);ctx.lineTo(xR,y);ctx.stroke();
      ctx.fillStyle='rgba('+C.inkR+',.42)';ctx.fillText(String(s),xL-16,y);
    }
    ctx.save();ctx.translate(xL-34,yOf(3.5));ctx.rotate(-Math.PI/2);ctx.textAlign='center';ctx.fillStyle='rgba('+C.inkR+',.34)';ctx.fillText('score',0,0);ctx.restore();
    var yc=yOf(CUT);ctx.setLineDash([5,5]);ctx.strokeStyle='rgba('+C.accR+',.6)';ctx.beginPath();ctx.moveTo(xL,yc);ctx.lineTo(xR,yc);ctx.stroke();ctx.setLineDash([]);

    var n=Math.floor((xR-xL)/STEP)+1,xs=new Float32Array(n),hs=new Float32Array(n),ms=new Float32Array(n);
    for(var k=0;k<n;k++){var x=xL+k*STEP,tau=tauOf(x);xs[k]=x;hs[k]=yOf(at(tau,'h'));ms[k]=yOf(at(tau,'m'))}

    for(var k=0;k<n-1;k++){                                           // the area between the traces, gold where the decision flips
      var hm=(hs[k]+hs[k+1])/2,mm=(ms[k]+ms[k+1])/2,gap=Math.abs(hm-mm)/(H-PT-PB)*5;
      var fl=(hm-yc)*(mm-yc)<0,edge=smooth(xL,xL+60,xs[k])*smooth(xR+2,xR-40,xs[k]);
      ctx.fillStyle=fl?'rgba('+C.accR+','+(.34*edge).toFixed(3)+')':'rgba('+C.inkR+','+((.04+.13*Math.min(1,gap))*edge).toFixed(3)+')';
      ctx.beginPath();ctx.moveTo(xs[k],hs[k]);ctx.lineTo(xs[k+1],hs[k+1]);ctx.lineTo(xs[k+1],ms[k+1]);ctx.lineTo(xs[k],ms[k]);ctx.closePath();ctx.fill();
    }
    function trace(arr,color,w,halo){
      ctx.lineJoin='round';
      ctx.beginPath();for(var k=0;k<n;k++)k?ctx.lineTo(xs[k],arr[k]):ctx.moveTo(xs[k],arr[k]);
      ctx.strokeStyle=halo;ctx.lineWidth=w*4;ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=w;ctx.stroke();
    }
    trace(ms,'rgba('+C.inkR+',.9)',1.5,'rgba('+C.inkR+',.07)');
    trace(hs,C.accHex,2.1,'rgba('+C.accR+',.10)');
    for(var i=0;i<S.length;i++){                                      // a dot for every response
      var x=xR-(now-S[i].t)*SPEED;if(x<xL+4||x>xR)continue;
      ctx.fillStyle=C.paperHex;
      ctx.beginPath();ctx.arc(x,yOf(S[i].h),2.8,0,6.283);ctx.fill();ctx.strokeStyle=C.accHex;ctx.lineWidth=1.2;ctx.stroke();
      ctx.beginPath();ctx.arc(x,yOf(S[i].m),2.6,0,6.283);ctx.fill();ctx.strokeStyle='rgba('+C.inkR+',.9)';ctx.stroke();
    }
    var i=0;ctx.textAlign='center';                                   // one flag per run of flips
    while(i<S.length){
      if(!S[i].flip){i++;continue}
      var j=i;while(j+1<S.length&&S[j+1].flip)j++;
      var tc=(S[i].t+S[j].t)/2,x=xR-(now-tc)*SPEED;
      if(x>xL+60&&x<xR-30){
        var a=smooth(xL+50,xL+170,x)*smooth(xR-30,xR-110,x),top=Math.min(yOf(at(tc,'h')),yOf(at(tc,'m'))),yy=Math.max(PT-6,top-26);
        ctx.strokeStyle='rgba('+C.accR+','+(a*.6).toFixed(2)+')';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,yy+8);ctx.lineTo(x,top-4);ctx.stroke();
        ctx.fillStyle='rgba('+C.accR+','+(a*.95).toFixed(2)+')';ctx.fillText('decision flips',x,yy);
      }
      i=j+1;
    }
    ctx.strokeStyle='rgba('+C.inkR+',.22)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(xR,PT-14);ctx.lineTo(xR,H-PB+10);ctx.stroke();   // live edge
    var hN=at(now,'h'),mN=at(now,'m'),yh=yOf(hN),ym=yOf(mN);
    ctx.fillStyle=C.accHex;ctx.beginPath();ctx.arc(xR,yh,3.6,0,6.283);ctx.fill();
    ctx.fillStyle=C.inkHex;ctx.beginPath();ctx.arc(xR,ym,3.2,0,6.283);ctx.fill();
    var yh2=yh,ym2=ym;if(Math.abs(yh2-ym2)<26){var mid=(yh2+ym2)/2,sg=yh2<ym2?-1:1;yh2=mid+sg*13;ym2=mid-sg*13}
    ctx.textAlign='left';ctx.fillStyle=C.accHex;ctx.fillText('Human '+hN.toFixed(1),xR+16,yh2);
    ctx.fillStyle='rgba('+C.inkR+',.92)';ctx.fillText('Automated '+mN.toFixed(1),xR+16,ym2);
    ctx.textAlign='left';ctx.fillStyle='rgba('+C.accR+',.85)';ctx.fillText('cut score',xL+4,yOf(CUT)-6);   // the dashed line, named in place (no legend)

    if(px>=xL&&px<=xR&&py>=0&&py<=H){                                 // the listener
      var tau=tauOf(px),h=at(tau,'h'),m=at(tau,'m'),flip=(h>=CUT)!==(m>=CUT);
      ctx.strokeStyle='rgba('+C.accR+',.65)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(px,PT-14);ctx.lineTo(px,H-PB+10);ctx.stroke();
      ctx.fillStyle=C.accHex;ctx.beginPath();ctx.arc(px,yOf(h),3.8,0,6.283);ctx.fill();
      ctx.fillStyle=C.inkHex;ctx.beginPath();ctx.arc(px,yOf(m),3.4,0,6.283);ctx.fill();
      tip.innerHTML='<b>Response · '+Math.max(0,Math.round((now-tau)/DT))+' ago</b>Human <i>'+h.toFixed(1)+'</i><br>Automated <i>'+m.toFixed(1)+'</i><br>Difference <em>'+Math.abs(h-m).toFixed(1)+'</em>'+(flip?'<br><em>Decision flips at the cut score</em>':'<br>Same side of the cut score');
      placeTip(tip,box,px,py);
    }else tip.style.display='none';
  }
  function frame(){if(!running)return;draw(performance.now()/1000);raf=requestAnimationFrame(frame)}
  function start(){if(running||RM||document.hidden||!vis)return;running=true;raf=requestAnimationFrame(frame)}
  function stop(){running=false;cancelAnimationFrame(raf)}
  box.addEventListener('pointermove',function(e){var r=box.getBoundingClientRect();px=e.clientX-r.left;py=e.clientY-r.top;if(!running)draw(staticNow)},{passive:true});
  box.addEventListener('pointerleave',function(){px=py=-1;tip.style.display='none';if(!running)draw(staticNow)});
  new ResizeObserver(size).observe(box);
  document.addEventListener('themechange',function(){if(!running)draw(staticNow)});
  size();
  new IntersectionObserver(function(es){vis=es[0].isIntersecting;vis?start():stop()}).observe(box);   // no work while off screen
  document.addEventListener('visibilitychange',function(){document.hidden?stop():start()});
  start();
})();
