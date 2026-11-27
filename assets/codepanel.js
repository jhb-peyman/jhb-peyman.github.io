// Research page: a small editor that types the core model of four studies, runs it, and prints the
// numbers each paper reports, with a chart of them. The code is a sketch written for the page; every
// number in the console and the charts is copied from the paper named in the caption.
//
// Behaviour: a file is typed out the first time it is shown, and only while the panel is on screen and
// the browser tab is visible (it pauses otherwise and carries on where it stopped). Opening a file that
// has already played shows it finished; Run plays it again. Nothing switches files by itself.
(function(){
  var S=[
    {file:'cfa_ethics.R',lang:'r',env:'R 4.6.1 \u00b7 lavaan \u00b7 semTools \u00b7 psych',doi:'10.21203/rs.3.rs-11286301/v1',ref:'GenAI ethics instruments',
     cap:'GenAI ethics instruments: confirmatory factor models for ordinal items and omega reliability. Fit indices and omegas as reported in the paper (N = 148).',
     code:'library(lavaan); library(semTools)\n\n# six factors, ordinal Likert items\nfit <- cfa(model, data = items, ordered = TRUE,\n           estimator = "WLSMV")\nfitMeasures(fit, c("cfi.scaled", "tli.scaled",\n                   "rmsea.scaled", "srmr"))\ncompRelSEM(fit)    # omega for each scale',
     out:'  cfi    tli  rmsea   srmr\n0.923  0.917  0.068  0.089\n\nethical integrity self_eff intrinsic extrinsic\n   0.82      0.87     0.94      0.91      0.86',
     chart:{kind:'bars',title:'Omega by scale',axis:'omega',max:1,ticks:[0,.5,1],fmt:2,items:[['Ethical judgment',.82],['Institutional integrity',.87],['GenAI self-efficacy',.94],['Intrinsic motivation',.91],['Extrinsic motivation',.86]]}},
    {file:'gaps_glmm.R',lang:'r',env:'R 4.4.3 \u00b7 lme4 \u00b7 MASS',doi:'10.48550/arXiv.2610.02582',ref:'Acoustic gap placement',
     cap:'Acoustic gaps: a gap or not at every word boundary, with crossed random intercepts for speakers and passage positions. Estimates as reported in the paper (115 speakers, 250 ms threshold).',
     code:'library(lme4)\n\n# one row per speaker x word boundary: was there a gap?\nm <- glmer(gap ~ group * unpunctuated +\n             (1 | speaker) + (1 | position),\n           data = boundaries, family = binomial)\nexp(fixef(m))["groupMandarin:unpunctuatedTRUE"]\n# plus a count model of unpunctuated gaps per speaker',
     out:'# group x unpunctuated, odds ratio\nOR  9.44   95% CI [5.23, 17.02]\n# unpunctuated gaps per speaker, Mandarin vs English L1\nRR 11.98   95% CI [6.53, 22.00]',
     chart:{kind:'forest',title:'Mandarin vs English L1',axis:'ratio, log scale',ref:1,lo:1,hi:40,ticks:[1,3,10,30],items:[['Gap at unpunctuated boundary (OR)',9.44,5.23,17.02],['Unpunctuated gaps per speaker (RR)',11.98,6.53,22.00]]}},
    {file:'firth_reporting.R',lang:'r',env:'R \u00b7 logistf',ref:'Too Few to Count, white paper (2026)',
     cap:'Too Few to Count: does a Kansas district publish an English learner reading result? Firth penalized logistic regression, 2023-24 (203 districts). Odds ratios as reported in the white paper.',
     code:'library(logistf)\n\n# 1 = the district has a public EL reading result\nm1 <- logistf(reports ~ rural, data = districts)\nm2 <- logistf(reports ~ rural + log1p(el_enrollment),\n              data = districts)\nexp(cbind(OR = coef(m1), confint(m1)))["rural", ]\nexp(cbind(OR = coef(m2), confint(m2)))["rural", ]',
     out:'# rural, unadjusted\nOR 0.08   95% CI [0.04, 0.16]   p < .001\n# rural, adjusted for EL enrollment\nOR 0.66   95% CI [0.18, 2.49]   p = .528',
     chart:{kind:'forest',title:'Rural vs nonrural districts',axis:'odds ratio, log scale',ref:1,lo:.02,hi:5,ticks:[.03,.1,.3,1,3],items:[['Unadjusted',.08,.04,.16],['Adjusted for EL enrollment',.66,.18,2.49]]}},
    {file:'mfcc_rf.py',lang:'py',env:'Python 3.10 \u00b7 librosa \u00b7 scikit-learn 1.2.2',doi:'10.48550/arXiv.2504.13765',ref:'MFCC framework',
     cap:'MFCC framework: 13 MFCCs per speaker (20 ms frames, 10 ms hop at 44.1 kHz), then random forests on all 13 and on MFCC 1, 2 and 5. Accuracies and Wilson intervals as reported in the paper.',
     code:'import librosa\nfrom sklearn.ensemble import RandomForestClassifier\n\ny, sr = librosa.load(path, sr=44100)\nmfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13,\n                            n_fft=882, hop_length=441)\nX = mfcc.mean(axis=1)             # one vector per speaker\n\nfull    = RandomForestClassifier().fit(X_train, y_train)\nreduced = RandomForestClassifier().fit(X_train[:, [0, 1, 4]], y_train)',
     out:'all 13 MFCCs   accuracy 0.528   95% CI [0.370, 0.680]\nMFCC 1, 2, 5   accuracy 0.750   95% CI [0.589, 0.863]\nMcNemar test   p = 0.039',
     chart:{kind:'bars',title:'Classification accuracy',axis:'accuracy',max:1,ticks:[0,.5,1],fmt:'%',items:[['All 13 MFCCs',.528,.370,.680],['MFCC 1, 2, 5',.75,.589,.8625]]}}
  ];
  var box=document.getElementById('codeP');if(!box)return;
  var $=function(id){return document.getElementById(id)};
  var tabs=box.querySelector('.snip-tabs'),ed=$('codeEd'),lines=$('codeL'),out=$('codeO'),svg=$('codeV'),head=$('codeH'),cap=$('codeC'),
      tip=$('codeTip'),env=$('codeEnv'),refEl=$('codeRef'),dot=$('codeDot'),runArea=box.querySelector('.snip-run'),
      btnRun=$('codeRun'),btnCopy=$('codeCopy'),ICON=window.SNIP_ICONS||{};
  var RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cur=0,played=[],inView=false,queue=[],timer=0,waiting=false,seen=false;

  // ---------------------------------------------------------------- syntax colouring, one line at a time
  function esc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
  var KW={r:/\b(library|function|TRUE|FALSE|NULL)\b/g,py:/\b(import|from|as|def|return|for|in)\b/g};
  function hlLine(line,lang){
    var i=line.indexOf('#'),body=i>=0?line.slice(0,i):line,com=i>=0?line.slice(i):'';
    body=body.split(/("[^"]*"?)/).map(function(p,j){
      if(j%2)return '<span class="t-s">'+esc(p)+'</span>';
      return esc(p).replace(KW[lang],'<span class="t-k">$1</span>')
        .replace(/(^|[^\w.])(\d+(?:\.\d+)?)\b/g,'$1<span class="t-n">$2</span>')
        .replace(/([A-Za-z_][\w.]*)(?=\()/g,'<span class="t-f">$1</span>')
        .replace(/(&lt;-|\||~|\*)/g,'<span class="t-o">$1</span>')
        .replace(/(\b[a-z_]+)(?=\s=\s)/g,'<span class="t-a">$1</span>');
    }).join('');
    return body+(com?'<span class="t-c">'+esc(com)+'</span>':'');
  }
  // the editor: one row per line (number and code together, so they can never drift apart)
  function drawCode(n,caret){
    var s=S[cur],src=s.code.slice(0,n).split('\n'),h='';
    src.forEach(function(line,i){
      var last=i===src.length-1;
      h+='<div class="ln'+(caret&&last?' at':'')+'"><span class="no">'+(i+1)+'</span><span class="tx">'+hlLine(line,s.lang)+(caret&&last?'<i class="t-cur"></i>':'')+'</span></div>';
    });
    lines.innerHTML=h;
  }
  var maxLines=Math.max.apply(null,S.map(function(s){return s.code.split('\n').length}));
  lines.style.setProperty('--rows',maxLines);

  // the console
  function cmd(s){return s.lang==='py'?'<span class="t-p">$</span> python '+s.file:'<span class="t-p">&gt;</span> source(<span class="t-s">"'+s.file+'"</span>)'}
  function prompt(s){return '<span class="t-p">'+(s.lang==='py'?'$':'&gt;')+'</span> <i class="t-cur"></i>'}
  function hlOut(t){return esc(t).replace(/(#.*)$/gm,'<span class="t-c">$1</span>').replace(/(^|[\s\[(=])(-?\d*\.\d+|\d+\.\d+)/g,'$1<span class="t-n">$2</span>')}
  function setDot(st){dot.className='snip-dot '+st;dot.title={idle:'Waiting',typing:'Typing',running:'Running',done:'Finished'}[st]||''}

  // ---------------------------------------------------------------- chart: one band per estimate, labels above the bands
  var NS='http://www.w3.org/2000/svg';
  function el(t,a,txt){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e}
  function fmt(v,f){return f==='%'?Math.round(v*100)+'%':v.toFixed(f||2).replace(/^0\./,'.')}
  function chart(c,anim){
    while(svg.firstChild)svg.removeChild(svg.firstChild);head.textContent=c.title;
    var W=Math.round(Math.max(220,Math.min(420,svg.getBoundingClientRect().width||300))),L=2,R=W-2,row=c.kind==='bars'&&c.items.length>3?36:44,band=c.kind==='bars'&&c.items.length>3?14:20,top=2;
    var H=top+c.items.length*row+30;svg.setAttribute('viewBox','0 0 '+W+' '+H);
    var x;
    if(c.kind==='bars'){x=function(v){return L+(R-L-40)*v/c.max}}
    else{var a=Math.log(c.lo),b=Math.log(c.hi);x=function(v){return L+10+(R-L-20)*(Math.log(v)-a)/(b-a)}}
    var axisY=top+c.items.length*row+2;
    c.items.forEach(function(it,i){
      var y=top+i*row,by=y+row-band-4,yc=by+band/2,d=i*170;
      var g=el('g',{class:'g-item','data-i':i});
      g.appendChild(el('rect',{x:0,y:y,width:W,height:row,class:'g-hit'}));
      g.appendChild(el('text',{x:L,y:by-5,class:'g-lab'},it[0]));
      g.appendChild(el('rect',{x:L,y:by,width:R-L,height:band,class:'g-band'}));
      c.ticks.forEach(function(t){g.appendChild(el('line',{x1:x(t),x2:x(t),y1:by,y2:by+band,class:'g-grid'}))});
      if(c.ref)g.appendChild(el('line',{x1:x(c.ref),x2:x(c.ref),y1:by-2,y2:by+band+2,class:'g-ref'}));
      var vx,anchor='start',lab;
      if(c.kind==='bars'){
        var w=Math.max(1,x(it[1])-L);
        g.appendChild(el('rect',{x:L,y:yc-band/2+3,width:w,height:band-6,class:'g-bar',style:'transform-origin:'+L+'px '+yc+'px;transition-delay:'+d+'ms'}));
        if(it.length>3){g.appendChild(el('line',{x1:x(it[2]),x2:x(it[3]),y1:yc,y2:yc,class:'g-ci g-anim',style:'transition-delay:'+(d+350)+'ms'}))}
        vx=x(it.length>3?it[3]:it[1])+6;lab=fmt(it[1],c.fmt);
      }else{
        var p=x(it[1]);
        g.appendChild(el('line',{x1:p,x2:x(it[2]),y1:yc,y2:yc,class:'g-ci g-draw',pathLength:1,style:'transition-delay:'+(d+120)+'ms'}));
        g.appendChild(el('line',{x1:p,x2:x(it[3]),y1:yc,y2:yc,class:'g-ci g-draw',pathLength:1,style:'transition-delay:'+(d+120)+'ms'}));
        g.appendChild(el('rect',{x:p-4.5,y:yc-4.5,width:9,height:9,class:'g-pt',style:'transform-origin:'+p+'px '+yc+'px;transition-delay:'+d+'ms'}));
        vx=x(it[3])+7;lab=String(it[1]);
        if(vx>W-30){vx=x(it[2])-7;anchor='end'}
      }
      g.appendChild(el('text',{x:vx,y:yc+3.5,'text-anchor':anchor,class:'g-val g-anim',style:'transition-delay:'+(d+400)+'ms'},lab));
      svg.appendChild(g);
    });
    c.ticks.forEach(function(t){svg.appendChild(el('text',{x:x(t),y:axisY+11,'text-anchor':'middle',class:'g-tick'},
      c.kind==='bars'?(c.fmt==='%'?Math.round(t*100)+'%':String(t)):String(t)))});
    if(c.axis)svg.appendChild(el('text',{x:R,y:axisY+25,'text-anchor':'end',class:'g-axis'},c.axis));
    if(anim){svg.classList.remove('on');void svg.getBoundingClientRect();requestAnimationFrame(function(){svg.classList.add('on')})}
    else svg.classList.add('on');
  }
  function clearChart(){while(svg.firstChild)svg.removeChild(svg.firstChild);head.textContent='';svg.classList.remove('on')}

  // ---------------------------------------------------------------- a small scheduler that waits while the panel is off screen
  function active(){return inView&&!document.hidden}
  function stopAll(){clearTimeout(timer);queue=[];waiting=false}
  function pump(){
    clearTimeout(timer);
    if(!queue.length){waiting=false;return}
    if(!active()){waiting=true;return}
    waiting=false;
    var a=queue.shift();a.f();timer=setTimeout(pump,a.d||0);
  }
  function later(){if(waiting&&active())pump()}

  // typing in tokens (words, spaces, punctuation) with an uneven rhythm, pausing at line ends
  function tokens(src){return src.match(/\n[ ]*|[A-Za-z_][\w.]*|\d+(?:\.\d+)?|"[^"\n]*"?|#[^\n]*|[ ]+|./g)||[]}
  function rnd(a,b){return a+Math.random()*(b-a)}

  function header(k){
    cur=k;var s=S[k];
    [].forEach.call(tabs.children,function(b,j){b.setAttribute('aria-selected',j===k?'true':'false');b.tabIndex=j===k?0:-1});
    var tb=tabs.children[k];if(tb){var l=tb.offsetLeft,r=l+tb.offsetWidth;                 // keep the open tab in view on narrow screens
      if(l<tabs.scrollLeft)tabs.scrollLeft=l-8;else if(r>tabs.scrollLeft+tabs.clientWidth)tabs.scrollLeft=r-tabs.clientWidth+8}
    ed.setAttribute('aria-labelledby','snip-tab-'+k);
    cap.textContent=s.cap;env.textContent=s.env;tip.style.display='none';
    refEl.innerHTML=s.doi?'<a href="https://doi.org/'+s.doi+'" target="_blank" rel="noopener">'+s.ref+' \u2197</a>':esc(s.ref);
  }
  function finished(k){
    stopAll();header(k);var s=S[k];
    drawCode(s.code.length,false);out.innerHTML=cmd(s)+'\n'+hlOut(s.out)+'\n'+prompt(s);
    runArea.classList.add('on');chart(s.chart,false);setDot('done');played[k]=true;
  }
  function play(k){
    stopAll();header(k);var s=S[k];
    if(RM){finished(k);return}
    drawCode(0,true);out.innerHTML='';runArea.classList.remove('on');clearChart();setDot('idle');
    var n=0,tk=tokens(s.code);
    queue.push({d:350,f:function(){setDot('typing')}});
    tk.forEach(function(t){
      var d=t.charAt(0)==='\n'?rnd(130,210):t.charAt(0)==='#'?rnd(160,240):/^ +$/.test(t)?0:/^[\w"]/.test(t)?rnd(38,85):rnd(22,48);
      queue.push({d:d,f:function(){n+=t.length;drawCode(n,true)}});
    });
    runSteps(k,true);
    pump();
  }
  // run: lines light up in turn, the console prints, the chart draws
  function runSteps(k,afterTyping){
    var s=S[k],L=s.out.split('\n');
    queue.push({d:afterTyping?420:0,f:function(){drawCode(s.code.length,false);setDot('running');btnRun.classList.add('busy')}});
    var rows=s.code.split('\n');
    rows.forEach(function(r,i){queue.push({d:r.trim()&&r.trim().charAt(0)!=='#'?70:0,f:function(){
      var all=lines.children;for(var j=0;j<all.length;j++)all[j].classList.toggle('exec',j===i)}})});
    queue.push({d:140,f:function(){[].forEach.call(lines.children,function(x){x.classList.remove('exec')});runArea.classList.add('on');out.innerHTML=cmd(s)}});
    queue.push({d:520,f:function(){out.innerHTML=cmd(s)+'\n<span class="t-wait"></span>'}});
    L.forEach(function(_,i){queue.push({d:i<L.length-1?110:220,f:function(){out.innerHTML=cmd(s)+'\n'+hlOut(L.slice(0,i+1).join('\n'))}})});
    queue.push({d:0,f:function(){out.innerHTML=cmd(s)+'\n'+hlOut(s.out)+'\n'+prompt(s);chart(s.chart,true);setDot('done');btnRun.classList.remove('busy');played[k]=true}});
  }
  function show(k){if(played[k])finished(k);else play(k)}

  // ---------------------------------------------------------------- tabs, buttons, visibility
  S.forEach(function(s,k){var b=document.createElement('button');b.type='button';b.setAttribute('role','tab');b.id='snip-tab-'+k;b.setAttribute('aria-controls','codeEd');
    b.innerHTML=(ICON[s.lang]||'')+'<span>'+s.file+'</span>';
    b.addEventListener('click',function(){if(k!==cur||!played[k]&&!queue.length)show(k)});
    b.addEventListener('keydown',function(e){var j=-1;if(e.key==='ArrowRight')j=(k+1)%S.length;else if(e.key==='ArrowLeft')j=(k+S.length-1)%S.length;else if(e.key==='Home')j=0;else if(e.key==='End')j=S.length-1;
      if(j>=0){e.preventDefault();show(j);tabs.children[j].focus()}});
    tabs.appendChild(b)});
  btnRun.addEventListener('click',function(){
    if(RM){finished(cur);return}
    var s=S[cur];stopAll();
    if(!played[cur]){header(cur)}                      // still typing: finish the code at once, then run it
    drawCode(s.code.length,false);out.innerHTML='';clearChart();runArea.classList.remove('on');
    inView=true;runSteps(cur,false);pump();
  });
  btnCopy.addEventListener('click',function(){var t=S[cur].code,lab=btnCopy.querySelector('span');
    (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){lab.textContent='Copied'},function(){lab.textContent='Select'}).then(function(){setTimeout(function(){lab.textContent='Copy'},1600)})});

  // start (or carry on) only while most of the panel is on screen and the browser tab is visible
  header(0);drawCode(0,true);setDot('idle');
  if(RM){finished(0)}
  var io=new IntersectionObserver(function(es){
    var e=es[0],vh=window.innerHeight||1;
    inView=e.isIntersecting&&(e.intersectionRatio>=.6||e.intersectionRect.height>=vh*.6);
    if(inView&&!seen){seen=true;if(!RM&&!played[cur]&&!queue.length){play(cur);return}}
    later();
  },{threshold:[0,.2,.4,.6,.8,1]});
  io.observe(box);
  document.addEventListener('visibilitychange',later);

  // values on hover
  svg.addEventListener('pointermove',function(e){var g=e.target.closest&&e.target.closest('.g-item');if(!g){tip.style.display='none';return}
    var it=S[cur].chart.items[+g.dataset.i],c=S[cur].chart,r=svg.parentNode.getBoundingClientRect();
    var v=c.fmt==='%'?Math.round(it[1]*1000)/10+'%':String(it[1]),ci=it.length>3?(c.fmt==='%'?' ['+Math.round(it[2]*1000)/10+'%, '+Math.round(it[3]*1000)/10+'%]':' ['+it[2]+', '+it[3]+']'):'';
    tip.innerHTML='<b>'+esc(it[0])+'</b>'+v+(ci?' <span>95% CI'+ci+'</span>':'');tip.style.display='block';
    var x=e.clientX-r.left+12,y=e.clientY-r.top+12;if(x+tip.offsetWidth>r.width)x=e.clientX-r.left-tip.offsetWidth-12;tip.style.left=x+'px';tip.style.top=y+'px'});
  svg.addEventListener('pointerleave',function(){tip.style.display='none'});
  // keep the chart at its real size when the window is resized
  var rz=0,lastW=0;window.addEventListener('resize',function(){clearTimeout(rz);rz=setTimeout(function(){
    var w=Math.round(svg.getBoundingClientRect().width);if(w&&w!==lastW&&svg.firstChild&&svg.classList.contains('on')){lastW=w;chart(S[cur].chart,false)}},150)});
})();
