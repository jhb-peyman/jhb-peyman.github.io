// Live spectrogram for the home page, laid out like a phonetics workstation.
//  - Simulated mode: a source-filter speech synthesiser reads the research question phone by phone
//    (harmonics under formant resonances, fricative and burst noise, nasal murmur, coarticulation,
//    a falling pitch contour with accents). Above the mel spectrogram: the pitch track and formant
//    tracks; below it: a word tier and an IPA phone tier.
//  - Microphone mode (opt-in): the visitor's own voice, analysed in the browser (FFT to mel bands,
//    YIN pitch, LPC formants, a voiced / voiceless / pause tier). Nothing is recorded or sent.
// Needs figures.js for the theme colours (C, mix).
(function(){
  var box=document.getElementById('vizS');if(!box)return;
  var spec=document.getElementById('specS'),ov=document.getElementById('ovS'),tip=document.getElementById('tipS');
  var btn=document.getElementById('micS'),modeLab=document.getElementById('modeS'),stat=document.getElementById('statS');
  var meter=document.createElement('span');meter.className='sp-meter';meter.hidden=true;meter.innerHTML='<i></i>';meter.title='Microphone input level';
  if(modeLab)modeLab.after(meter);
  var sx=spec.getContext('2d'),ox=ov.getContext('2d'),RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var NB=128,FMAX=8000,CPS=70,SC=1.6,RING=4096,TIERS=38;
  function clamp(v,a,b){return v<a?a:v>b?b:v}
  function sm(a,b,x){var t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t)}
  function mel(f){return 2595*Math.log10(1+f/700)}
  function imel(m){return 700*(Math.pow(10,m/2595)-1)}
  function rgba(c,a){return 'rgba('+Math.round(c[0])+','+Math.round(c[1])+','+Math.round(c[2])+','+a+')'}
  var MM=mel(FMAX),FREQ=new Float32Array(NB),BWD=new Float32Array(NB);
  for(var i=0;i<NB;i++){FREQ[i]=imel((i+.5)/NB*MM);BWD[i]=imel((i+1)/NB*MM)-imel(i/NB*MM)}

  // ---------------------------------------------------------------- colour
  var LUT=new Uint8Array(256*3);
  function buildLUT(){
    var st=[[0,C.paper],[.2,mix(C.paper,C.acc,.1)],[.45,mix(C.paper,C.acc,.62)],[.68,C.acc],[.88,mix(C.acc,C.ink,.62)],[1,C.ink]];
    for(var i=0;i<256;i++){var v=i/255,k=0;while(k<st.length-2&&v>st[k+1][0])k++;var a=st[k],b=st[k+1],t=(v-a[0])/(b[0]-a[0]);
      for(var c=0;c<3;c++)LUT[i*3+c]=a[1][c]+(b[1][c]-a[1][c])*t}
  }
  buildLUT();

  // ---------------------------------------------------------------- phones (formants in Hz, typical adult values)
  var PH={
    'i':{t:'V',F:[270,2290,3010]},'ɪ':{t:'V',F:[390,1990,2550]},'ɛ':{t:'V',F:[530,1840,2480]},'æ':{t:'V',F:[660,1720,2410]},
    'ʌ':{t:'V',F:[640,1190,2390]},'ɔ':{t:'V',F:[570,840,2410]},'ə':{t:'V',F:[500,1500,2500]},'ɚ':{t:'V',F:[490,1350,1690]},
    'eɪ':{t:'D',F:[480,1950,2600],G:[350,2250,2900]},'oʊ':{t:'D',F:[520,920,2400],G:[420,800,2300]},'aʊ':{t:'D',F:[760,1250,2500],G:[460,1000,2300]},
    'w':{t:'A',F:[300,610,2200]},'l':{t:'A',F:[360,1300,2700]},'r':{t:'A',F:[420,1300,1600]},
    'm':{t:'N',F:[270,1100,2200],Z:1000},'n':{t:'N',F:[270,1700,2600],Z:1500},'ŋ':{t:'N',F:[270,2000,2800],Z:2600},
    's':{t:'F',lo:3900,pk:6300,hi:8000,a:.42},'z':{t:'F',lo:3900,pk:6300,hi:8000,a:.28,v:1},
    'ʃ':{t:'F',lo:1900,pk:3100,hi:6500,a:.45},'ʒ':{t:'F',lo:1900,pk:3100,hi:6500,a:.3,v:1},
    'f':{t:'F',lo:1200,pk:5000,hi:8000,a:.22,flat:1},'v':{t:'F',lo:1200,pk:5000,hi:8000,a:.16,flat:1,v:1},'ð':{t:'F',lo:1000,pk:4500,hi:8000,a:.13,flat:1,v:1},
    'h':{t:'H'},
    'p':{t:'S',b:[300,2000,.25]},'t':{t:'S',b:[3200,6500,.34]},'k':{t:'S',b:[1500,2600,.32]},'d':{t:'S',b:[3200,6500,.26],v:1},'g':{t:'S',b:[1500,2600,.26],v:1}
  };
  // The tagline, in IPA ("'" marks the stressed vowel)
  var PHRASES=[
    [['how',['h',"'aʊ"]],['well',['w',"'ɛ",'l']],['automated',["'ɔ",'t','ə','m','eɪ','t','ɪ','d']],['scoring',['s','k',"'ɔ",'r','ɪ','ŋ']],
     ['judges',['d','ʒ',"'ʌ",'d','ʒ','ɪ','z']],['spoken',['s','p',"'oʊ",'k','ə','n']],['English',["'ɪ",'ŋ','g','l','ɪ','ʃ']]],
    [['and',["'æ",'n','d']],['whether',['w',"'ɛ",'ð','ɚ']],['it',['ɪ','t']],['judges',['d','ʒ',"'ʌ",'d','ʒ','ɪ','z']],
     ['everyone',["'ɛ",'v','r','i','w','ʌ','n']],['fairly',['f',"'ɛ",'r','l','i']]]
  ];
  function jit(){return .85+.3*Math.random()}
  var queue=[],segs={},words={},segId=0,wordId=0,phraseNo=0,phrase={t:0,T:1,acc:[]};
  function buildPhrase(){
    var P=PHRASES[phraseNo++%PHRASES.length],out=[],t=0,acc=[];
    P.forEach(function(w,wi){
      var wid=++wordId;words[wid]={lab:w[0]};
      w[1].forEach(function(raw,pi){
        var st=raw.charAt(0)==="'",lab=st?raw.slice(1):raw,ph=PH[lab],d;
        if(ph.t==='V')d=(st?.15:.068)*jit();else if(ph.t==='D')d=(st?.19:.12)*jit();else if(ph.t==='A')d=.06*jit();
        else if(ph.t==='N')d=.065*jit();else if(ph.t==='F')d=(ph.v?.085:.115)*jit();else if(ph.t==='H')d=.06;
        else{var nx=w[1][pi+1]||'',asp=!ph.v&&nx.charAt(0)==="'"?.045:.014;d=.055+.012+asp}
        var last=wi===P.length-1&&pi>=w[1].length-2&&(ph.t==='V'||ph.t==='D');if(last)d*=1.45;
        var seg={id:++segId,lab:lab,ph:ph,st:st,dur:d,word:wid,t0:t};
        if(ph.t==='S'){seg.cl=.055;seg.asp=d-.067}
        if(st)acc.push(t+d/2);
        out.push(seg);t+=d;
      });
    });
    out.push({id:++segId,lab:'',ph:{t:'P'},dur:.42+.25*Math.random(),word:0,t0:t});
    for(var k=0;k<out.length;k++){out[k].next=out[k+1];segs[out[k].id]=out[k];delete segs[out[k].id-600]}
    phrase={t:0,T:t,acc:acc};
    return out;
  }
  // synthesiser state
  var S={F:[500,1500,2500],av:0,an:0,f0:120,cur:null,u:0};
  function nextVowelF(seg){for(var s=seg.next,n=0;s&&n<4;s=s.next,n++)if(s.ph.F&&(s.ph.t==='V'||s.ph.t==='D'))return s.ph.F;return S.F}
  var colP=new Float32Array(NB);
  function reson(f,F,B){var a=F*F-f*f;return F*F/Math.sqrt(a*a+B*B*f*f)}
  function synthColumn(dt){
    if(!S.cur||S.u>=S.cur.dur){if(!queue.length)queue=buildPhrase();S.cur=queue.shift();S.u=0}
    var g=S.cur,ph=g.ph,u=S.u,Ft=S.F,avT=0,anT=0,shape=null;
    S.u+=dt;phrase.t+=dt;
    switch(ph.t){
      case 'V':Ft=ph.F;avT=g.st?1:.72;break;
      case 'D':var q=sm(.15,.9,u/g.dur);Ft=[ph.F[0]+(ph.G[0]-ph.F[0])*q,ph.F[1]+(ph.G[1]-ph.F[1])*q,ph.F[2]+(ph.G[2]-ph.F[2])*q];avT=g.st?1:.75;break;
      case 'A':Ft=ph.F;avT=.62;break;
      case 'N':Ft=ph.F;avT=.5;break;
      case 'F':Ft=nextVowelF(g);avT=ph.v?.3:0;anT=ph.a;shape='fric';break;
      case 'H':Ft=nextVowelF(g);anT=.32;shape='asp';break;
      case 'S':Ft=nextVowelF(g);
        if(u<g.cl){avT=ph.v?.14:0}
        else if(u<g.cl+.012){anT=ph.b[2];shape='burst'}
        else{anT=.3;shape='asp';avT=ph.v?.4:0}break;
      default:avT=0;
    }
    var kf=1-Math.exp(-dt/.028);for(var k=0;k<3;k++)S.F[k]+=(Ft[k]-S.F[k])*kf;
    S.av+=(avT-S.av)*(1-Math.exp(-dt/(avT>S.av?.012:.03)));
    S.an+=(anT-S.an)*(1-Math.exp(-dt/.006));
    var p=clamp(phrase.t/phrase.T,0,1),f0=138-42*p;
    phrase.acc.forEach(function(tc,j){var d=(phrase.t-tc)/.1;f0+=(j===0?34:24)*Math.exp(-d*d)});
    S.f0=f0*(1+.006*Math.sin(phrase.t*31)+.004*(Math.random()-.5));
    var F=S.F,B=[80,100,140],av=S.av,an=S.an,f0=S.f0;
    for(var i=0;i<NB;i++){
      var f=FREQ[i],P=1e-6*(.5+Math.random());
      if(av>.01){
        var env=1/(1+Math.pow(f/260,1.5));
        for(var k=0;k<3;k++)env*=reson(f,F[k],B[k]);
        env*=reson(f,3500,260)*reson(f,4500,330);
        if(ph.t==='N'){env*=(1-.85*Math.exp(-Math.pow((f-ph.Z)/220,2)))*(f>700?.3:1)}
        var bw=BWD[i],d=Math.abs(((f/f0+.5)%1)-.5)*f0,sig=Math.max(bw*.6,16),comb=Math.exp(-(d/sig)*(d/sig)),m=clamp((bw/f0-.35)/.8,0,1);
        comb=comb*(1-m)+m*.55;
        P+=av*av*env*env*comb;
      }
      if(an>.01){
        var sh=0;
        if(shape==='fric'){sh=sm(ph.lo*.8,ph.lo,f)*(1-sm(ph.hi,ph.hi*1.06,f));if(!ph.flat)sh*=.18+.82*Math.exp(-Math.pow((f-ph.pk)/(ph.pk*.3),2))}
        else if(shape==='burst'){sh=sm(ph.b[0]*.7,ph.b[0],f)*(1-sm(ph.b[1],ph.b[1]*1.5,f))}
        else{var e2=1/(1+Math.pow(f/900,1.2));for(var k=0;k<3;k++)e2*=reson(f,F[k],B[k]*1.6);sh=.22*e2}
        var rn=Math.random();P+=an*an*sh*sh*(.12+.88*rn*rn);
      }
      colP[i]=P;
    }
    return {f0:av>.25?f0:0,F:[F[0],F[1],F[2]],av:av,seg:g.id,word:g.word,kind:av>.25?2:an>.05?1:0};
  }

  // ---------------------------------------------------------------- microphone analysis
  var mic=null;   // {ctx, an, stream, fb, tb, sr, map, top}
  function buildMap(sr,n){
    var hz=sr/(2*n),map=[];
    for(var b=0;b<NB;b++){var lo=imel(b/NB*MM)/hz,hi=imel((b+1)/NB*MM)/hz,c=FREQ[b]/hz;map.push(hi-lo<2?{c:c}:{lo:Math.max(1,Math.floor(lo)),hi:Math.min(n-1,Math.ceil(hi))})}
    return map;
  }
  function decimate(buf,D){var n=Math.floor(buf.length/D),o=new Float32Array(n);for(var i=0;i<n;i++){var s=0;for(var j=0;j<D;j++)s+=buf[i*D+j];o[i]=s/D}return o}
  function yin(x,sr){
    var tmin=Math.floor(sr/400),tmax=Math.floor(sr/70),Wn=x.length-tmax,d=new Float32Array(tmax+2);if(Wn<64)return 0;
    for(var tau=1;tau<=tmax;tau++){var s=0;for(var j=0;j<Wn;j++){var v=x[j]-x[j+tau];s+=v*v}d[tau]=s}
    var run=0;for(tau=1;tau<=tmax;tau++){run+=d[tau];d[tau]=run?d[tau]*tau/run:1}
    for(tau=tmin;tau<tmax;tau++)if(d[tau]<.25){while(tau+1<tmax&&d[tau+1]<d[tau])tau++;var a=d[tau-1],b=d[tau],c=d[tau+1],den=a-2*b+c;return sr/(tau+(den?.5*(a-c)/den:0))}
    return 0;
  }
  // Formants, the way Praat does it: low-pass filter and downsample to 12 kHz, pre-emphasis from 50 Hz,
  // LPC (order 12, autocorrelation), then solve for the filter's poles and read each one's frequency and
  // bandwidth. Poles wider than 900 Hz are not formants. Tested against known vowels and against Praat.
  var FIRC={};
  function lowpassDecimate(x,D){            // windowed-sinc low-pass at 90% of the new Nyquist, then keep every D-th sample
    var h=FIRC[D];
    if(!h){var L=D*64+1,M=(L-1)/2,fc=.45/D,s=0;h=new Float32Array(L);
      for(var i=0;i<L;i++){var k=i-M,v=k?Math.sin(2*Math.PI*fc*k)/(Math.PI*k):2*fc;v*=.54-.46*Math.cos(2*Math.PI*i/(L-1));h[i]=v;s+=v}
      for(i=0;i<L;i++)h[i]/=s;FIRC[D]=h}
    var L=h.length,M=(L-1)>>1,n=Math.floor(x.length/D),o=new Float32Array(n);
    for(var j=0;j<n;j++){var c=j*D,a=0,i0=Math.max(0,M-c),i1=Math.min(L,x.length-c+M);for(var i=i0;i<i1;i++)a+=h[i]*x[c-M+i];o[j]=a}
    return o;
  }
  function polyRoots(a){                     // all roots of z^p + a1 z^(p-1) + ... + ap (Aberth-Ehrlich iteration)
    var p=a.length-1,re=new Float64Array(p),im=new Float64Array(p);
    for(var k=0;k<p;k++){var t=2*Math.PI*k/p+.4;re[k]=.9*Math.cos(t);im[k]=.9*Math.sin(t)}
    for(var it=0;it<80;it++){var mx=0;
      for(k=0;k<p;k++){var zr=re[k],zi=im[k],pr=1,pi=0,dr=0,di=0;
        for(var j=1;j<=p;j++){var ndr=dr*zr-di*zi+pr,ndi=dr*zi+di*zr+pi;dr=ndr;di=ndi;var npr=pr*zr-pi*zi+a[j],npi=pr*zi+pi*zr;pr=npr;pi=npi}
        var m=dr*dr+di*di;if(!m)continue;var nr=(pr*dr+pi*di)/m,ni=(pi*dr-pr*di)/m,sr=0,si=0;
        for(j=0;j<p;j++)if(j!==k){var ur=zr-re[j],ui=zi-im[j],um=ur*ur+ui*ui;if(um){sr+=ur/um;si-=ui/um}}
        var qr=1-(nr*sr-ni*si),qi=-(nr*si+ni*sr),qm=qr*qr+qi*qi;if(!qm)continue;
        var wr=(nr*qr+ni*qi)/qm,wi=(ni*qr-nr*qi)/qm;re[k]-=wr;im[k]-=wi;mx=Math.max(mx,wr*wr+wi*wi)}
      if(mx<1e-20)break}
    return [re,im];
  }
  function formants(x,sr){
    var n=x.length,p=12,y=new Float64Array(n),al=Math.exp(-2*Math.PI*50/sr);
    for(var i=0;i<n;i++)y[i]=(x[i]-(i?al*x[i-1]:0))*(.54-.46*Math.cos(2*Math.PI*i/(n-1)));
    var r=new Float64Array(p+1);for(var k=0;k<=p;k++){var s=0;for(i=k;i<n;i++)s+=y[i]*y[i-k];r[k]=s}
    if(r[0]<=0)return null;r[0]*=1.0001;
    var a=new Float64Array(p+1),tmp=new Float64Array(p+1),e=r[0];a[0]=1;
    for(i=1;i<=p;i++){var acc=r[i];for(var j=1;j<i;j++)acc+=a[j]*r[i-j];var kk=-acc/e;tmp.set(a);for(j=1;j<i;j++)a[j]=tmp[j]+kk*tmp[i-j];a[i]=kk;e*=1-kk*kk;if(e<=0)return null}
    var R=polyRoots(a),c=[];
    for(k=0;k<p;k++){var im=R[1][k];if(im<=0)continue;
      var f=Math.atan2(im,R[0][k])*sr/(2*Math.PI),bw=-Math.log(Math.hypot(R[0][k],im))*sr/Math.PI;
      if(f>150&&f<sr/2-100&&bw>0&&bw<900)c.push(f)}
    c.sort(function(u,v){return u-v});
    return c.length>=3?c.slice(0,3):null;
  }
  function micColumn(){
    var A=mic.an;if(mic.ctx.state!=='running'&&mic.ctx.resume)mic.ctx.resume();
    A.getFloatFrequencyData(mic.fb);A.getFloatTimeDomainData(mic.tb);
    var pk=0;for(var i=0;i<mic.tb.length;i+=8){var v=Math.abs(mic.tb[i]);if(v>pk)pk=v}
    var lvl=clamp((20*Math.log10(pk+1e-9)+60)/60,0,1);meter.firstChild.style.width=(lvl*100).toFixed(0)+'%';
    if(pk>1e-4){if(!mic.heard){mic.heard=1;note(mic.okMsg)}}
    else if(!mic.heard&&!mic.rebuilt&&performance.now()-mic.t0>1500){rebuildCtx()}
    else if(!mic.heard&&performance.now()-mic.t0>3500&&!mic.warned){mic.warned=1;
      var tr=mic.stream.getAudioTracks()[0],why=mic.ctx.state!=='running'?'The audio engine is '+mic.ctx.state+'; click the spectrogram once to start it.':tr&&tr.muted?'The browser reports the microphone as muted.':'The microphone is connected ('+(tr&&tr.label||'unnamed input')+') but sends silence. On a Mac, check System Settings, Privacy &amp; Security, Microphone, and that this input is not muted.';
      note('I can\u2019t hear anything yet. '+why)}
    var fb=mic.fb,top=-200;
    for(var b=0;b<NB;b++){var m=mic.map[b],P;
      if(m.c!==undefined){var i0=Math.floor(m.c),t=m.c-i0;P=Math.pow(10,(fb[i0]*(1-t)+fb[i0+1]*t)/10)}
      else{P=0;for(var i=m.lo;i<=m.hi;i++)P+=Math.pow(10,fb[i]/10);P/=(m.hi-m.lo+1)}
      if(!(P>0))P=1e-12;colP[b]=P;var db=10*Math.log10(P+1e-12);if(db>top)top=db}
    mic.top=Math.max(top,mic.top-.03,-62);                       // recent loudest sound (peak hold, about 2 dB/s decay)
    if(mic.floor===undefined)mic.floor=-90;                      // room noise level: follows quiet frames, ignores speech
    if(top>-110){var g=top-mic.floor;mic.floor+=g<0?g*.3:g<15?g*.04:.005}
    var span=mic.top-mic.floor;if(span<18)mic.top=mic.floor+18;
    var rms=0;for(var i=0;i<mic.tb.length;i++)rms+=mic.tb[i]*mic.tb[i];rms=Math.sqrt(rms/mic.tb.length);
    var loud=top>mic.floor+10,x2=decimate(mic.tb,2),f0=(rms>.0015&&loud)?yin(x2,mic.sr/2):0,Fm=null;
    // pitch clean-up: fold octave jumps back towards the running pitch, then take a 3-frame median
    var lp=mic.lastF0||0;
    if(f0&&lp){var r=f0/lp;if(r>1.75&&r<2.3)f0/=2;else if(r<.57&&r>.43)f0*=2}
    var hist=mic.fh||(mic.fh=[]);hist.push(f0);if(hist.length>3)hist.shift();
    if(f0){var nz=hist.filter(function(v){return v>0}).sort(function(a,b){return a-b});if(nz.length>=2)f0=nz[Math.floor(nz.length/2)];
      if(lp&&Math.abs(f0-lp)/lp>.35&&mic.voicedRun>2)f0=0;}
    mic.voicedRun=f0?(mic.voicedRun||0)+1:0;if(f0)mic.lastF0=f0;else if(!loud)mic.lastF0=0;
    if(mic.voicedRun<3)f0=0;   // the first frames of a voiced stretch are unreliable (onsets and fades), so the line starts once pitch is stable
    if(f0)Fm=formants(lowpassDecimate(mic.tb,4),mic.sr/4);
    // formant clean-up: median of the last three frames, so a single stray pole does not make a dot jump
    var fq=mic.fq||(mic.fq=[]);fq.push(Fm);if(fq.length>3)fq.shift();
    if(Fm){var ok=fq.filter(function(v){return v});if(ok.length>=2)Fm=[0,1,2].map(function(k){var v=ok.map(function(q){return q[k]}).sort(function(a,b){return a-b});return v[Math.floor(v.length/2)]})}
    dbg.top=top;dbg.f0=f0;
    return {f0:f0,F:Fm||[0,0,0],av:f0?1:0,seg:0,word:0,kind:f0?2:loud?1:0};
  }
  function startMic(){
    if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){note('This browser does not offer a microphone to web pages.');return}
    // The audio context is created and resumed inside the click itself; browsers keep a context that is
    // created later (after the permission prompt) suspended, and a suspended analyser only hears silence.
    var AC=window.AudioContext||window.webkitAudioContext,ctx=new AC();
    if(ctx.resume)ctx.resume();
    note('Waiting for you to allow the microphone…');
    navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}}).then(function(stream){
      var go=function(){
        var src=ctx.createMediaStreamSource(stream),an=ctx.createAnalyser(),mute=ctx.createGain();
        an.fftSize=2048;an.smoothingTimeConstant=0;mute.gain.value=0;
        src.connect(an);an.connect(mute);mute.connect(ctx.destination);   // a silent path to the output keeps the graph running in every browser
        tapRecorder(ctx,src,mute);
        mic={ctx:ctx,an:an,stream:stream,src:src,fb:new Float32Array(an.frequencyBinCount),tb:new Float32Array(an.fftSize),sr:ctx.sampleRate,map:buildMap(ctx.sampleRate,an.frequencyBinCount),top:-45,heard:0,t0:performance.now()};
        btn.classList.add('on');btn.querySelector('span').textContent='Stop microphone';modeLab.textContent='your microphone';
        var tr=stream.getAudioTracks()[0];
        mic.okMsg='Listening through <b>'+(tr&&tr.label?tr.label.replace(/</g,''):'your microphone')+'</b>. Say a long "aaa", hum, or try "sss" and "shh". Press Stop when you are done and you can play it back. Your voice stays on your computer.';
        note(mic.okMsg);meter.hidden=false;
        VAL.fill(0);H0.fill(0);HAV.fill(0);HF.fill(0);HK.fill(0);HS.fill(0);HW.fill(0);repaintAll();   // a clean slate, so what appears is clearly the visitor's voice
        dbg.cols=0;dbg.err='';stop();start();showDbg();
      };
      ctx.state==='running'?go():ctx.resume().then(go,go);
    },function(err){ctx.close();var n=err&&err.name||'Error';
      note(n==='NotAllowedError'?'The microphone is blocked for this page. Allow it from the icon in the address bar, then try again.':
           n==='NotFoundError'?'No microphone was found on this computer.':'The microphone could not start: '+n+(err&&err.message?' ('+String(err.message).replace(/</g,'')+')':'')+'.')});
  }
  // Some browsers (Safari) deliver only silence to an audio context that existed before the permission
  // was granted. If nothing is heard after 1.5 s, build a fresh context for the same microphone stream once.
  function rebuildCtx(){
    mic.rebuilt=1;
    try{
      var AC=window.AudioContext||window.webkitAudioContext,ctx=new AC();if(ctx.resume)ctx.resume();
      var src=ctx.createMediaStreamSource(mic.stream),an=ctx.createAnalyser(),mute=ctx.createGain();
      an.fftSize=2048;an.smoothingTimeConstant=0;mute.gain.value=0;src.connect(an);an.connect(mute);mute.connect(ctx.destination);rec.chunks=[];rec.len=0;tapRecorder(ctx,src,mute);
      try{mic.ctx.close()}catch(e){}
      mic.ctx=ctx;mic.an=an;mic.src=src;mic.sr=ctx.sampleRate;mic.fb=new Float32Array(an.frequencyBinCount);mic.tb=new Float32Array(an.fftSize);mic.map=buildMap(ctx.sampleRate,an.frequencyBinCount);mic.t0=performance.now();
    }catch(e){dbg.err='rebuild: '+(e&&e.message||e)}
  }
  function stopMic(){
    if(!mic)return;mic.stream.getTracks().forEach(function(t){t.stop()});try{mic.ctx.close()}catch(e){}mic=null;
    meter.hidden=true;btn.classList.remove('on');btn.querySelector('span').textContent='Try again';
    stop();review=true;modeLab.textContent='your voice';
    playBtn.hidden=!rec.len;
    note(rec.len?'That was you. Press Play to hear it while a line moves across the picture. The recording only lives in this page and is gone when you leave or try again.':'Nothing was recorded that time. Try again and speak a little closer to the microphone.');
    holdThenResume();
  }
  // ---------------------------------------------------------------- recording and playback
  var rec={chunks:[],len:0,sr:48000,max:15},review=false,resumeT=0,player=null,playX=-1;
  function tapRecorder(ctx,src,out){
    rec.sr=ctx.sampleRate;
    var sp=(ctx.createScriptProcessor||ctx.createJavaScriptNode).call(ctx,4096,1,1);
    sp.onaudioprocess=function(e){
      if(!mic)return;var d=new Float32Array(e.inputBuffer.getChannelData(0));rec.chunks.push(d);rec.len+=d.length;
      while(rec.len>rec.max*rec.sr&&rec.chunks.length>1){rec.len-=rec.chunks.shift().length}
    };
    src.connect(sp);sp.connect(out);
  }
  function holdThenResume(){clearTimeout(resumeT);resumeT=setTimeout(resumeSim,30000)}   // the visitor's picture stays at least 30 s after they finish
  function resumeSim(){
    if(player)return holdThenResume();
    review=false;playBtn.hidden=true;btn.querySelector('span').textContent='Try your own voice';modeLab.textContent='simulated speech';note(null);start();
  }
  function stopPlayback(){if(!player)return;try{player.src.stop()}catch(e){}try{player.ctx.close()}catch(e){}player=null;playX=-1;
    playBtn.classList.remove('on');playBtn.querySelector('span').textContent='Play back';overlay();holdThenResume()}
  function playBack(){
    if(player){stopPlayback();return}
    if(!rec.len)return;
    var vis=Math.max(1,(BW-2)/CPS),secs=Math.min(rec.len/rec.sr,vis),n=Math.floor(secs*rec.sr);   // what is on screen
    var AC=window.AudioContext||window.webkitAudioContext,ctx=new AC();if(ctx.resume)ctx.resume();
    var buf=ctx.createBuffer(1,n,rec.sr),ch=buf.getChannelData(0),pos=n,peak=0;
    for(var k=rec.chunks.length-1;k>=0&&pos>0;k--){var c=rec.chunks[k],take=Math.min(c.length,pos);ch.set(c.subarray(c.length-take),pos-take);pos-=take}
    for(var i=0;i<n;i++){var a=Math.abs(ch[i]);if(a>peak)peak=a}
    var g=ctx.createGain();g.gain.value=peak>0?Math.min(8,.8/peak):1;      // quiet microphones are brought up to a comfortable level
    var src=ctx.createBufferSource();src.buffer=buf;src.connect(g);g.connect(ctx.destination);
    player={ctx:ctx,src:src,t0:0,secs:secs};clearTimeout(resumeT);
    playBtn.classList.add('on');playBtn.querySelector('span').textContent='Stop';
    src.onended=function(){stopPlayback()};
    var begin=function(){player.t0=ctx.currentTime;src.start();requestAnimationFrame(tickPlay)};
    ctx.state==='running'?begin():ctx.resume().then(begin,begin);
  }
  function tickPlay(){
    if(!player)return;var el=player.ctx.currentTime-player.t0;
    playX=W-Math.max(0,player.secs-el)*CPS*SC;overlay();
    if(el<player.secs+.05)requestAnimationFrame(tickPlay);
  }
  var playBtn=document.createElement('button');playBtn.type='button';playBtn.className='sp-mic sp-play';playBtn.hidden=true;
  playBtn.innerHTML='<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M8 5.5v13l11-6.5z"/></svg><span>Play back</span>';
  if(btn){btn.parentNode.insertBefore(playBtn,btn);playBtn.addEventListener('click',playBack)}
  var defaultNote=stat?stat.innerHTML:'';
  function note(t){if(!stat)return;stat.innerHTML=t===null?defaultNote:'<span class="lg"><i class="lg-f0"></i>pitch (f0)</span><span class="lg"><i class="lg-fm"></i>formants</span> '+t}
  if(btn)btn.addEventListener('click',function(){if(mic){stopMic();return}stopPlayback();clearTimeout(resumeT);review=false;playBtn.hidden=true;rec.chunks=[];rec.len=0;startMic()});

  // ---------------------------------------------------------------- history
  var VAL=new Uint8Array(RING*NB),H0=new Float32Array(RING),HF=new Float32Array(RING*3),HAV=new Float32Array(RING),HS=new Int32Array(RING),HW=new Int32Array(RING),HK=new Uint8Array(RING),col=0;
  var LO=-46,HI=10;
  function pushColumn(info,isMic){
    var idx=col%RING,lo=isMic?Math.max(mic.floor+4,mic.top-50):LO,hi=isMic?mic.top+1:HI,gam=isMic?.8:1.15;
    for(var i=0;i<NB;i++){var db=10*Math.log10(colP[i]+1e-12),v=clamp((db-lo)/(hi-lo),0,1);VAL[idx*NB+i]=Math.pow(v,gam)*255|0}
    H0[idx]=info.f0;HF[idx*3]=info.F[0];HF[idx*3+1]=info.F[1];HF[idx*3+2]=info.F[2];HAV[idx]=info.av;HS[idx]=info.seg;HW[idx]=info.word;HK[idx]=info.kind;
    col++;
  }
  var BW=0,W=0,H=0,HS_=0,lastW=0;
  function paintCols(n){
    if(n<=0)return;n=Math.min(n,BW);
    var img=sx.createImageData(n,NB),pd=img.data;
    for(var c=0;c<n;c++){var idx=(col-n+c+RING)%RING;
      for(var i=0;i<NB;i++){var o=((NB-1-i)*n+c)*4,l=VAL[idx*NB+i]*3;pd[o]=LUT[l];pd[o+1]=LUT[l+1];pd[o+2]=LUT[l+2];pd[o+3]=255}}
    if(n<BW)sx.drawImage(spec,n,0,BW-n,NB,0,0,BW-n,NB);
    sx.putImageData(img,BW-n,0);
  }
  function repaintAll(){var n=Math.min(BW,col);sx.fillStyle=rgba(C.paper,1);sx.fillRect(0,0,BW,NB);paintCols(n)}

  // ---------------------------------------------------------------- overlay
  function yOf(f){return HS_*(1-mel(f)/MM)}
  function xOf(c){return W-(col-1-c)*SC}
  var P0=60,P1=280;function yP(f){return HS_*(1-(Math.log(f/P0)/Math.log(P1/P0))*.82)-HS_*.04}
  function fmt(f){return f>=1000?(f/1000).toFixed(f>=10000?0:1).replace(/\.0$/,'')+' kHz':Math.round(f)+' Hz'}
  var px=-1,py=-1;
  function overlay(){
    if(!W)return;ox.clearRect(0,0,W,H);
    var first=Math.max(0,col-Math.floor(W/SC)),ink=C.ink,acc=C.acc,pap=C.paper;
    ox.font='500 10px "IBM Plex Mono",monospace';ox.textBaseline='middle';
    [500,1000,2000,4000,8000].forEach(function(f){var y=yOf(f);if(y<10)y=10;
      ox.strokeStyle=rgba(ink,.07);ox.beginPath();ox.moveTo(0,Math.round(y)+.5);ox.lineTo(W,Math.round(y)+.5);ox.stroke();
      var lab=fmt(f),tw=ox.measureText(lab).width;ox.fillStyle=rgba(pap,.75);ox.fillRect(4,y-7,tw+8,14);ox.fillStyle=rgba(ink,.55);ox.textAlign='left';ox.fillText(lab,8,y)});
    // formant tracks
    for(var c=first;c<col;c+=2){var idx=c%RING;if(HAV[idx]<.45)continue;var x=xOf(c);
      for(var k=0;k<3;k++){var f=HF[idx*3+k];if(!f)continue;var y=yOf(f);ox.fillStyle=rgba(pap,.92);ox.fillRect(x-1.1,y-1.1,2.2,2.2)}}
    // pitch track
    ox.lineWidth=3.6;ox.strokeStyle=rgba(pap,.7);ox.lineJoin='round';
    for(var pass=0;pass<2;pass++){ox.beginPath();var on=false;
      for(var c=first;c<col;c++){var f=H0[c%RING],x=xOf(c);if(f>0){var y=yP(f);on?ox.lineTo(x,y):ox.moveTo(x,y);on=true}else on=false}
      ox.stroke();ox.lineWidth=1.7;ox.strokeStyle=rgba(acc,1)}
    ox.textAlign='right';ox.fillStyle=rgba(acc,1);
    [100,200].forEach(function(f){var y=yP(f);ox.fillStyle=rgba(pap,.75);var tw=ox.measureText(f+' Hz').width;ox.fillRect(W-tw-12,y-7,tw+8,14);ox.fillStyle=rgba(acc,.9);ox.fillText(f+' Hz',W-8,y)});
    // time ticks
    ox.textAlign='center';var c0=col-1-Math.floor(W/SC);c0=c0-(c0%CPS);
    for(var c=c0;c<col;c+=CPS){if(c<first)continue;var x=xOf(c);if(x<70||x>W-60)continue;
      ox.strokeStyle=rgba(ink,.25);ox.beginPath();ox.moveTo(x,HS_-6);ox.lineTo(x,HS_);ox.stroke();
      ox.fillStyle=rgba(ink,.45);ox.fillText('−'+Math.round((col-1-c)/CPS)+' s',x,HS_-13)}
    // tiers
    var ty=HS_,th=TIERS/2;ox.fillStyle=rgba(pap,1);ox.fillRect(0,ty,W,TIERS);
    ox.strokeStyle=rgba(ink,.18);ox.lineWidth=1;ox.beginPath();ox.moveTo(0,ty+.5);ox.lineTo(W,ty+.5);ox.moveTo(0,ty+th+.5);ox.lineTo(W,ty+th+.5);ox.moveTo(0,H-.5);ox.lineTo(W,H-.5);ox.stroke();
    if(mic||review){runs(first,function(i){return HK[i%RING]},function(v){return v===2?'voiced':v===1?'voiceless':''},ty,TIERS,'500 9.5px "IBM Plex Mono",monospace',true)}
    else{runs(first,function(i){return HW[i%RING]},function(v){return v&&words[v]?words[v].lab:''},ty,th,'500 10px "IBM Plex Mono",monospace',false);
      runs(first,function(i){return HS[i%RING]},function(v){var s=segs[v];return s&&s.lab?(s.st?'ˈ':'')+s.lab:''},ty+th,th,'15px "Times New Roman","Charis SIL","Doulos SIL",serif',false)}
    if(playX>=0){ox.fillStyle=rgba(acc,.1);ox.fillRect(playX,0,W-playX,HS_);ox.strokeStyle=rgba(acc,1);ox.lineWidth=2;ox.beginPath();ox.moveTo(Math.round(playX),0);ox.lineTo(Math.round(playX),H);ox.stroke();ox.lineWidth=1}
    if(px>=0&&py>=0&&px<=W&&py<=H){ox.strokeStyle=rgba(acc,.75);ox.lineWidth=1;ox.beginPath();ox.moveTo(Math.round(px)+.5,0);ox.lineTo(Math.round(px)+.5,H);if(py<HS_){ox.moveTo(0,Math.round(py)+.5);ox.lineTo(W,Math.round(py)+.5)}ox.stroke();readout()}
    else tip.style.display='none';
  }
  function runs(first,get,label,y,h,font,mono){
    ox.font=font;ox.textAlign='center';ox.textBaseline='middle';var start=first,cur=get(first);
    for(var c=first+1;c<=col;c++){var v=c<col?get(c):-1;
      if(v!==cur){var x1=xOf(start)-SC/2,x2=xOf(c-1)+SC/2;
        if(start>first){ox.strokeStyle=rgba(C.ink,.22);ox.beginPath();ox.moveTo(Math.round(x1)+.5,y+2);ox.lineTo(Math.round(x1)+.5,y+h-2);ox.stroke()}
        var lab=label(cur);if(lab){var tw=ox.measureText(lab).width;if(x2-x1>tw+4){ox.fillStyle=rgba(C.ink,mono?.55:.82);ox.fillText(lab,clamp((x1+x2)/2,tw/2+2,W-tw/2-2),y+h/2+.5)}}
        start=c;cur=v}}
  }
  function readout(){
    var c=col-1-Math.round((W-px)/SC);if(c<0||c<col-RING){tip.style.display='none';return}
    var idx=c%RING,ago=((col-1-c)/CPS).toFixed(1),h='<b>'+(py<HS_?fmt(imel((1-py/HS_)*MM))+' · ':'')+ago+' s ago</b>';
    if(!mic&&!review){var s=segs[HS[idx]],w=words[HW[idx]];h+=s&&s.lab?'<i>'+(w?w.lab:'')+'</i> · phone <em>['+(s.st?'ˈ':'')+s.lab+']</em><br>':'<i>pause</i><br>'}
    else h+=(HK[idx]===2?'<i>voiced</i>':HK[idx]===1?'<i>voiceless</i>':'<i>quiet</i>')+'<br>';
    if(H0[idx]>0)h+='pitch <em>'+Math.round(H0[idx])+' Hz</em><br>';
    if(HAV[idx]>.45&&HF[idx*3])h+='F1 <i>'+Math.round(HF[idx*3])+'</i> · F2 <i>'+Math.round(HF[idx*3+1])+'</i> · F3 <i>'+Math.round(HF[idx*3+2])+'</i>';
    tip.innerHTML=h;tip.style.display='block';
    var tw=tip.offsetWidth,thh=tip.offsetHeight,l=px+16,t=py+16;if(l+tw>W-8)l=px-tw-16;if(t+thh>H-8)t=py-thh-16;tip.style.left=Math.max(8,l)+'px';tip.style.top=Math.max(8,t)+'px';
  }

  // ---------------------------------------------------------------- sizing and loop
  function layout(force){
    var w=box.clientWidth,h=box.clientHeight;if(!w||!h)return;W=w;H=h;HS_=H-TIERS;
    spec.style.height=HS_+'px';
    if(force||w!==lastW){lastW=w;BW=Math.max(120,Math.round(W/SC));spec.width=BW;spec.height=NB;
      if(col<BW&&!mic){var dt=1/CPS;while(col<BW){var inf=synthColumn(dt);pushColumn(inf,false)}}
      repaintAll()}
    var d=Math.max(1,Math.min(devicePixelRatio||1,Math.sqrt(2.4e6/(W*H))));ov.width=Math.round(W*d);ov.height=Math.round(H*d);ox.setTransform(d,0,0,d,0,0);
    overlay();
  }
  var running=false,raf=0,last=0,acc=0,vis=true,userPaused=false,pauseS=document.getElementById('pauseS');
  if(pauseS){if(RM)pauseS.hidden=true;
    pauseS.addEventListener('click',function(){userPaused=!userPaused;pauseS.setAttribute('aria-pressed',userPaused);pauseS.textContent=userPaused?'Play':'Pause';
      if(userPaused&&!mic)stop();else start()})}
  if(btn&&window.MutationObserver){new MutationObserver(function(){btn.setAttribute('aria-pressed',btn.classList.contains('on'))}).observe(btn,{attributes:true,attributeFilter:['class']})}
  var dbg={cols:0,t:0,err:'',top:0,f0:0};
  function showDbg(){}
  function frame(ts){
    if(!running)return;var dt=Math.min((ts-last)/1000,.1);last=ts;acc+=dt*CPS;var n=Math.floor(acc);acc-=n;n=Math.min(n,8);
    raf=requestAnimationFrame(frame);          // scheduled first, so one failing frame can never stop the loop
    try{
      if(n>0){if(mic){var inf=micColumn();for(var k=0;k<n;k++)pushColumn(inf,true);dbg.cols+=n}else for(var k=0;k<n;k++)pushColumn(synthColumn(1/CPS),false);paintCols(n)}
      overlay();
      if(mic&&ts-dbg.t>500){dbg.t=ts;showDbg()}
    }catch(e){dbg.err=(e&&e.message||String(e)).slice(0,120);if(mic)showDbg()}
  }
  function start(){if(running||document.hidden||!vis||(RM&&!mic)||(review&&!mic)||(userPaused&&!mic))return;running=true;last=performance.now();raf=requestAnimationFrame(frame)}
  function stop(){running=false;cancelAnimationFrame(raf)}
  box.addEventListener('pointermove',function(e){var r=box.getBoundingClientRect();px=e.clientX-r.left;py=e.clientY-r.top;if(!running)overlay()},{passive:true});
  box.addEventListener('click',function(){if(mic&&mic.ctx.state!=='running')mic.ctx.resume()});
  box.addEventListener('pointerleave',function(){px=py=-1;tip.style.display='none';if(!running)overlay()});
  new ResizeObserver(function(){layout(false)}).observe(box);
  document.addEventListener('themechange',function(){buildLUT();repaintAll();overlay()});
  new IntersectionObserver(function(es){vis=es[0].isIntersecting;vis?start():stop()}).observe(box);
  document.addEventListener('visibilitychange',function(){document.hidden?stop():start()});
  layout(true);start();
})();
