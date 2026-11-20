// Small live figures for the publication list, drawn from each paper itself: its method, and where
// the paper reports them, its own numbers (cited in the comment above each figure). They run only while on screen, follow light and
// dark mode, and draw one still frame when the visitor prefers reduced motion. Needs figures.js (C).
(function(){
  var RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
  function rgba(c,a){return 'rgba('+Math.round(c[0])+','+Math.round(c[1])+','+Math.round(c[2])+','+(+a).toFixed(3)+')'}
  function mixc(a,b,t){return[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]}
  function hash(n){n=Math.sin(n*127.1+311.7)*43758.5453;return n-Math.floor(n)}
  function ease(t){t=Math.max(0,Math.min(1,t));return t*t*(3-2*t)}
  function cl(v,a,b){return v<a?a:v>b?b:v}
  function mono(x,size,col,align,base){x.font='500 '+size+'px "IBM Plex Mono",ui-monospace,monospace';x.fillStyle=col;x.textAlign=align||'left';x.textBaseline=base||'alphabetic'}
  function tag(x,t){mono(x,9,rgba(C.mute,1));x.fillText(t,8,14)}
  function ramp(v){v=cl(v,0,1);return v<.5?mixc(C.paper,C.acc,v*2*.9):mixc(C.acc,C.ink,(v-.5)*2*.6)}

  var A={};

  // shared: grow-hold-fade cycle and a small bar label
  function cyc(t,period){var c=t%period;return{g:ease(c/2.2),f:c>period-.7?(period-c)/.7:1}}

  // ---------------------------------------------------------------- R2 Acoustic gap placement (after its Fig 1A)
  // Share of speakers pausing (gap of 250 ms or more) at each of the 68 interword positions of the passage;
  // the seven punctuation-marked positions are shaded. Heights are read off the paper's Fig 1A.
  var GP=[3,14,20,26,34,49,58],GEN=[78,93,67,64,100,95,50],GZH=[74,97,83,76,86,85,58];
  function gapRate(i,zh){var k=GP.indexOf(i);if(k>=0)return zh?GZH[k]:GEN[k];
    if(i===41)return zh?33:24;if(!zh)return i===46?3:i===65?5:0;var v=hash(i*3.7);return v>.55?4+v*14:v*3}
  A.gap=function(x,w,h,t){
    tag(x,'gap rate at 68 positions');
    var c=cyc(t,9),x0=22,x1=w-8,y0=24,y1=h-18,pos=1+Math.floor(c.g*67.99);
    function X(i){return x0+(i-1)/67*(x1-x0)}function Y(v){return y1-v/100*(y1-y0)}
    GP.forEach(function(i){x.fillStyle=rgba(C.mute,.13);x.fillRect(X(i)-1.6,y0,3.2,y1-y0)});
    x.strokeStyle=rgba(C.rule,1);x.lineWidth=1;x.beginPath();x.moveTo(x0,y1+.5);x.lineTo(x1,y1+.5);x.stroke();
    mono(x,7,rgba(C.mute,1),'right','middle');x.fillText('100',x0-3,y0+2);x.fillText('0',x0-3,y1);
    [[true,rgba(C.acc,c.f),1.3],[false,rgba(C.ink,.7*c.f),.9]].forEach(function(L){
      x.strokeStyle=L[1];x.lineWidth=L[2];x.beginPath();
      for(var i=1;i<=pos;i++){var px=X(i),py=Y(gapRate(i,L[0]));i===1?x.moveTo(px,py):x.lineTo(px,py)}x.stroke();
    });
    mono(x,7,rgba(C.mute,1),'left','alphabetic');
    x.fillStyle=rgba(C.ink,.7);x.fillRect(x0,h-7,8,1.5);x.fillText('English L1',x0+11,h-4);
    x.fillStyle=rgba(C.acc,1);x.fillRect(x0+62,h-7,8,1.5);mono(x,7,rgba(C.mute,1),'left','alphabetic');x.fillText('Mandarin L1',x0+73,h-4);
  };

  // ---------------------------------------------------------------- R1 GenAI ethics (its Table 4)
  // Mean seriousness (1 to 5) of the seven GenAI behaviours; AI help on assignments was rated far
  // less serious than the same help during an exam.
  var ETH=[['fabricate data',4.55],['submit AI work',4.52],['AI help: exam',4.49,1],['rework peer work',4.47],['fake bibliography',4.16],['AI help: assignment',3.33,1],['paraphrase, no credit',3.11]];
  A.ethics=function(x,w,h,t){
    tag(x,'how serious? 1 to 5 · n = 149');
    var c=cyc(t,9),lx=100,bx1=w-24,y0=24,rh=(h-y0-6)/ETH.length;
    ETH.forEach(function(e,i){
      var y=y0+i*rh+rh/2,g=ease(c.g*1.6-i*.09),bw=(e[1]-1)/4*(bx1-lx)*g;
      mono(x,6.8,rgba(e[2]?C.ink:C.mute,e[2]?.9:1),'right','middle');x.fillText(e[0],lx-4,y);
      x.fillStyle=rgba(C.rule,1);x.fillRect(lx,y-.5,bx1-lx,1);
      x.fillStyle=e[2]?rgba(C.acc,c.f):rgba(C.ink,.45*c.f);x.fillRect(lx,y-2.5,bw,5);
      if(g>.95){mono(x,7,rgba(C.mute,c.f),'left','middle');x.fillText(e[1].toFixed(2),lx+bw+3,y)}
    });
  };

  // ---------------------------------------------------------------- P2 LLTM (its Table 2 and Δ²)
  // LLTM weights (η) of the reading predictors: positive weights make an item harder, negative easier.
  // The Q-matrix explained 77% of the variance in item difficulty (Δ² = .765).
  var LW=[['subtask',.654],['inferences',.445],['sentence',.134],['paraphrase',.125],['meaning',-.411],['comprehension',-.864],['decision',-1.26],['encode visuals',-1.702]];
  A.lltm=function(x,w,h,t){
    tag(x,'LLTM weights η · Δ² = .77');
    var c=cyc(t,9),lx=70,zx=lx+(w-8-lx)*(1.75/2.45),sc=(w-8-lx)/2.45,y0=24,rh=(h-y0-4)/LW.length;
    x.strokeStyle=rgba(C.mute,.6);x.lineWidth=1;x.beginPath();x.moveTo(zx+.5,y0-2);x.lineTo(zx+.5,h-4);x.stroke();
    LW.forEach(function(e,i){
      var y=y0+i*rh+rh/2,g=ease(c.g*1.6-i*.08),bw=e[1]*sc*g;
      mono(x,7,rgba(C.mute,1),'right','middle');x.fillText(e[0],lx-4,y);
      x.fillStyle=e[1]>0?rgba(C.acc,c.f):rgba(C.ink,.4*c.f);x.fillRect(Math.min(zx,zx+bw),y-2.5,Math.abs(bw),5);
    });
    mono(x,6.5,rgba(C.mute,1),'center','alphabetic');x.fillText('easier ←  → harder',zx-14,h-1);
  };

  // ---------------------------------------------------------------- P4 Hedges in book reviews (its Table 4)
  // Frequency of each hedging category in 240 reviews: native reviewers vs Malaysian reviewers.
  var HC=[['modal',1784,1112],['verb',828,556],['adj',360,152],['adv',176,20],['quant',664,380],['noun',328,348]];
  A.hedge=function(x,w,h,t){
    tag(x,'hedges · 240 reviews');
    var c=cyc(t,9),x0=10,x1=w-8,y0=26,y1=h-18,gw=(x1-x0)/HC.length,bw=(gw-6)/2;
    x.fillStyle=rgba(C.rule,1);x.fillRect(x0,y1,x1-x0,1);
    HC.forEach(function(e,i){
      var gx=x0+i*gw+2,g=ease(c.g*1.5-i*.08);
      [1,2].forEach(function(k){var bh=e[k]/1784*(y1-y0)*g;x.fillStyle=k===1?rgba(C.acc,c.f):rgba(C.ink,.35*c.f);x.fillRect(gx+(k-1)*(bw+1),y1-bh,bw,bh)});
      mono(x,7,rgba(C.mute,1),'center','alphabetic');x.fillText(e[0],gx+bw,y1+9);
    });
    mono(x,7,rgba(C.mute,1),'left','alphabetic');
    x.fillStyle=rgba(C.acc,1);x.fillRect(w-96,18,6,6);x.fillText('native',w-87,24);
    x.fillStyle=rgba(C.ink,.35);x.fillRect(w-52,18,6,6);mono(x,7,rgba(C.mute,1),'left','alphabetic');x.fillText('Malaysian',w-43,24);
  };

  // ---------------------------------------------------------------- P7 Audio-assisted reading (its Tables 6 and 11)
  // Post-test means adjusted for the pre-test (11.78 vs 8.62) and delayed post-test means (14.72 vs 6.63)
  // for the audio-assisted reading group (n = 18) and the reading-only group (n = 16).
  A.aar=function(x,w,h,t){
    tag(x,'test means · n = 34');
    var c=cyc(t,9),y0=24,y1=h-16,maxv=16,groups=[['post (adj.)',11.78,8.62],['delayed',14.72,6.63]],gx0=40,gw=(w-8-gx0)/2;
    mono(x,7,rgba(C.mute,1),'left','middle');
    x.fillStyle=rgba(C.acc,1);x.fillRect(8,y0+4,6,6);x.fillText('audio',8,y0+18);x.fillText('+ text',8,y0+27);
    x.fillStyle=rgba(C.ink,.35);x.fillRect(8,y0+40,6,6);mono(x,7,rgba(C.mute,1),'left','middle');x.fillText('text',8,y0+54);x.fillText('only',8,y0+63);
    x.fillStyle=rgba(C.rule,1);x.fillRect(gx0,y1,w-8-gx0,1);
    groups.forEach(function(gp,i){
      var gx=gx0+i*gw+8,bw=(gw-22)/2,g=ease(c.g*1.4-i*.15);
      [1,2].forEach(function(k){var v=gp[k],bh=v/maxv*(y1-y0)*g,bx=gx+(k-1)*(bw+3);
        x.fillStyle=k===1?rgba(C.acc,c.f):rgba(C.ink,.35*c.f);x.fillRect(bx,y1-bh,bw,bh);
        if(g>.95){mono(x,7,rgba(C.mute,c.f),'center','alphabetic');x.fillText(v.toFixed(1),bx+bw/2,y1-bh-2)}});
      mono(x,7,rgba(C.mute,1),'center','alphabetic');x.fillText(gp[0],gx+bw+1,y1+9);
    });
  };

  // ---------------------------------------------------------------- R3 Reproducible pipeline (its component list)
  var TERM=['$ python pipeline.py','› mp3 → wav, 44.1 kHz','› 13 MFCCs per frame','› mean per speaker','› t-tests, MANOVA, CDA','› random forest: full vs reduced','› accuracy, 95% CI, McNemar'];
  A.term=function(x,w,h,t){
    tag(x,'reproducible pipeline · python');
    var per=10,cc=t%per,chars=Math.floor(cc*26),y=30,lh=11.5,used=0;
    for(var i=0;i<TERM.length;i++){
      var L=TERM[i],n=Math.max(0,Math.min(L.length,chars-used));used+=L.length+6;if(n<=0&&i>0)break;
      mono(x,7.5,i===0?rgba(C.acc,1):rgba(C.ink,.75),'left','alphabetic');x.fillText(L.slice(0,n),8,y+i*lh);
      if(n<L.length||i===TERM.length-1){var tw=x.measureText(L.slice(0,n)).width;if(Math.floor(t*2.4)%2===0){x.fillStyle=rgba(C.acc,.9);x.fillRect(9+tw,y+i*lh-7,4,8)}break}
    }
  };

  A.mfcc=function(x,w,h,t,s){
    var NB=48,NC=13,cw=2,x0=8,x1=w-30,specT=22,specB=Math.round(h*.66),mT=specB+5,mB=h-6;
    var cols=Math.floor((x1-x0)/cw);
    if(!s.buf||s.cols!==cols){s.cols=cols;s.buf=[];s.mf=[];s.mean=new Array(NC).fill(0);s.n=0;s.segT=0;s.F=[500,1500,2500];s.Ft=[500,1500,2500];s.kind=1;s.v=0;s.nz=0;s.f0=120;s.last=0}
    var want=Math.floor(t*30);if(!s.last||want-s.last>cols)s.last=want-cols;
    var V=[[730,1090,2440],[270,2290,3010],[530,1840,2480],[300,870,2240],[660,1720,2410],[570,840,2410]];
    while(s.last<want){s.last++;
      if(s.segT<=0){var r=hash(s.last*1.37);s.kind=r<.58?1:r<.8?2:0;
        s.segT=s.kind===1?9+hash(s.last)*10:s.kind===2?5+hash(s.last+1)*5:4+hash(s.last+2)*6;s.Ft=V[Math.floor(hash(s.last*3.1)*V.length)]}
      s.segT--;
      for(var k=0;k<3;k++)s.F[k]+=(s.Ft[k]-s.F[k])*.22;
      s.v+=((s.kind===1?1:0)-s.v)*.35;s.nz+=((s.kind===2?1:0)-s.nz)*.5;s.f0=115+12*Math.sin(s.last*.05);
      var col=[];
      for(var b=0;b<NB;b++){
        var m=b/(NB-1)*2840,f=700*(Math.pow(10,m/2595)-1),I=0;
        if(s.v>.02){var e=.1*Math.exp(-f/2600);for(var k=0;k<3;k++){var d=(f-s.F[k])/(90+k*45);e+=(k===0?1:k===1?.8:.55)*Math.exp(-d*d)}
          var ct=cl(1.15-f/2600,.1,1),hm=Math.pow(Math.max(0,Math.cos(6.2832*f/s.f0)),6);I+=s.v*e*(.25+.75*(ct*hm+(1-ct)*.5))}
        if(s.nz>.02)I+=s.nz*(f>3200?.5:f>2500?.15:0)*(.55+.45*hash(s.last*13+b));
        I+=.035*hash(s.last*7+b*3)*(s.v+s.nz>.05?1:.4);
        col.push(cl(Math.pow(I*1.5,.6),0,1));
      }
      var mf=[];for(var c=1;c<=NC;c++){var sum=0;for(var b=0;b<NB;b++)sum+=Math.log(.03+col[b])*Math.cos(Math.PI*c*(b+.5)/NB);mf.push(sum/4)}
      s.buf.push(col);s.mf.push(mf);if(s.buf.length>cols){s.buf.shift();s.mf.shift()}
      if(s.kind){s.n++;for(var c=0;c<NC;c++)s.mean[c]+=(mf[c]-s.mean[c])/Math.min(s.n,150)}
    }
    var rh=(specB-specT)/NB;
    for(var j=0;j<s.buf.length;j++){var cx=x0+(cols-s.buf.length+j)*cw,col=s.buf[j];
      for(var b=0;b<NB;b++){var v=col[b];if(v<.1)continue;x.fillStyle=rgba(ramp(.08+.92*(v-.1)/.9),1);x.fillRect(cx,specB-(b+1)*rh,cw,rh+.5)}}
    x.strokeStyle=rgba(C.rule,1);x.lineWidth=1;x.beginPath();x.moveTo(x0,specB+.5);x.lineTo(x1,specB+.5);x.stroke();
    var mh=(mB-mT)/NC;
    function mcol(v){v=Math.tanh(v/3);return v>=0?mixc(C.paper,C.acc,.1+.9*v):mixc(C.paper,C.mute,.1+.7*-v)}
    for(var j=0;j<s.mf.length;j++){var cx=x0+(cols-s.mf.length+j)*cw;
      for(var c=0;c<NC;c++){x.fillStyle=rgba(mcol(s.mf[j][c]),1);x.fillRect(cx,mT+c*mh,cw,mh+.3)}}
    var wx=x0+(cols-1)*cw;x.strokeStyle=rgba(C.acc,1);x.strokeRect(wx-1.5,specT-1.5,cw+3,mB-specT+3);
    for(var c=0;c<NC;c++){x.fillStyle=rgba(mcol(s.mean[c]),1);x.fillRect(w-20,mT+c*mh,12,mh-.4)}
    x.strokeStyle=rgba(C.rule,1);x.strokeRect(w-20.5,mT-.5,13,mB-mT+1);
    tag(x,'spectrogram → 13 MFCCs → mean');
    mono(x,7.5,rgba(C.mute,1),'center','alphabetic');x.fillText('mean',w-14,mT-3);
  };

  // ---------------------------------------------------------------- runner
  var items=[],raf=0,last=0;
  function size(it){
    var r=it.cv.getBoundingClientRect(),d=Math.min(2,devicePixelRatio||1);
    if(!r.width)return;it.w=r.width;it.h=r.height;it.cv.width=Math.round(r.width*d);it.cv.height=Math.round(r.height*d);it.x.setTransform(d,0,0,d,0,0);
  }
  function draw(it,t){if(!it.w)return;it.x.clearRect(0,0,it.w,it.h);it.f(it.x,it.w,it.h,t,it.s)}
  function loop(ts){
    raf=0;var any=items.some(function(it){return it.vis});
    if(ts-last>30){last=ts;var t=ts/1000;items.forEach(function(it){if(it.vis)draw(it,t+it.off)})}
    if(any&&!document.hidden)raf=requestAnimationFrame(loop);
  }
  function kick(){if(!RM&&!raf)raf=requestAnimationFrame(loop)}
  var io=new IntersectionObserver(function(es){es.forEach(function(e){var it=e.target._it;it.vis=e.isIntersecting;if(RM||!it.vis)draw(it,5.5+it.off)});kick()});
  var ro=new ResizeObserver(function(es){es.forEach(function(e){var it=e.target._it;size(it);draw(it,performance.now()/1000+it.off)})});
  document.querySelectorAll('canvas[data-anim]').forEach(function(cv,i){
    var f=A[cv.dataset.anim];if(!f)return;
    var it={cv:cv,x:cv.getContext('2d'),f:f,s:{},vis:false,w:0,h:0,off:i*1.7};cv._it=it;items.push(it);
    size(it);draw(it,5.5+it.off);io.observe(cv);ro.observe(cv);
  });
  document.addEventListener('themechange',function(){items.forEach(function(it){draw(it,performance.now()/1000+it.off)})});
  document.addEventListener('visibilitychange',kick);
})();
