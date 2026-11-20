// Research page: a small editor that types the core model of four studies, "runs" it, and prints the
// numbers each paper reports, with a chart of them. The code is a sketch written for the page; every
// number in the console and the charts is copied from the paper named in the caption.
(function(){
  var S=[
    {file:'cfa_ethics.R',lang:'r',env:'R 4.6.1 \u00b7 lavaan \u00b7 semTools \u00b7 psych',doi:'10.21203/rs.3.rs-11286301/v1',ref:'GenAI ethics instruments',
     cap:'GenAI ethics instruments: confirmatory factor models for ordinal items and omega reliability. Fit indices and omegas as reported in the paper (N = 148).',
     code:'library(lavaan); library(semTools)\n\n# six factors, ordinal Likert items\nfit <- cfa(model, data = items, ordered = TRUE,\n           estimator = "WLSMV")\nfitMeasures(fit, c("cfi.scaled", "tli.scaled",\n                   "rmsea.scaled", "srmr"))\ncompRelSEM(fit)    # omega for each scale',
     out:'  cfi    tli  rmsea   srmr\n0.923  0.917  0.068  0.089\n\nethical integrity self_eff intrinsic extrinsic\n   0.82      0.87     0.94      0.91      0.86',
     chart:{kind:'bars',title:'Omega by scale',max:1,ticks:[0,.5,1],fmt:2,items:[['Ethical judgment',.82],['Institutional integrity',.87],['GenAI self-efficacy',.94],['Intrinsic motivation',.91],['Extrinsic motivation',.86]]}},
    {file:'gaps_glmm.R',lang:'r',env:'R 4.4.3 \u00b7 lme4 \u00b7 MASS',doi:'10.48550/arXiv.2610.02582',ref:'Acoustic gap placement',
     cap:'Acoustic gaps: a gap or not at every word boundary, with crossed random intercepts for speakers and passage positions. Estimates as reported in the paper (115 speakers, 250 ms threshold).',
     code:'library(lme4)\n\n# one row per speaker x word boundary: was there a gap?\nm <- glmer(gap ~ group * unpunctuated +\n             (1 | speaker) + (1 | position),\n           data = boundaries, family = binomial)\nexp(fixef(m))["groupMandarin:unpunctuatedTRUE"]\n# plus a count model of unpunctuated gaps per speaker',
     out:'# group x unpunctuated, odds ratio\nOR  9.44   95% CI [5.23, 17.02]\n# unpunctuated gaps per speaker, Mandarin vs English L1\nRR 11.98   95% CI [6.53, 22.00]',
     chart:{kind:'forest',title:'Mandarin vs English L1',ref:1,lo:1,hi:40,ticks:[1,3,10,30],items:[['Gap at unpunctuated boundary (OR)',9.44,5.23,17.02],['Unpunctuated gaps per speaker (RR)',11.98,6.53,22.00]]}},
    {file:'firth_reporting.R',lang:'r',env:'R \u00b7 logistf',ref:'Too Few to Count, white paper (2026)',
     cap:'Too Few to Count: does a Kansas district publish an English learner reading result? Firth penalized logistic regression, 2023-24 (203 districts). Odds ratios as reported in the white paper.',
     code:'library(logistf)\n\n# 1 = the district has a public EL reading result\nm1 <- logistf(reports ~ rural, data = districts)\nm2 <- logistf(reports ~ rural + log1p(el_enrollment),\n              data = districts)\nexp(cbind(OR = coef(m1), confint(m1)))["rural", ]\nexp(cbind(OR = coef(m2), confint(m2)))["rural", ]',
     out:'# rural, unadjusted\nOR 0.08   95% CI [0.04, 0.16]   p < .001\n# rural, adjusted for EL enrollment\nOR 0.66   95% CI [0.18, 2.49]   p = .528',
     chart:{kind:'forest',title:'Rural vs nonrural districts',ref:1,lo:.02,hi:5,ticks:[.03,.1,.3,1,3],items:[['Unadjusted',.08,.04,.16],['Adjusted for EL enrollment',.66,.18,2.49]]}},
    {file:'mfcc_rf.py',lang:'py',env:'Python 3.10 \u00b7 librosa \u00b7 scikit-learn 1.2.2',doi:'10.48550/arXiv.2504.13765',ref:'MFCC framework',
     cap:'MFCC framework: 13 MFCCs per speaker (20 ms frames, 10 ms hop at 44.1 kHz), then random forests on all 13 and on MFCC 1, 2 and 5. Accuracies and Wilson intervals as reported in the paper.',
     code:'import librosa\nfrom sklearn.ensemble import RandomForestClassifier\n\ny, sr = librosa.load(path, sr=44100)\nmfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13,\n                            n_fft=882, hop_length=441)\nX = mfcc.mean(axis=1)             # one vector per speaker\n\nfull    = RandomForestClassifier().fit(X_train, y_train)\nreduced = RandomForestClassifier().fit(X_train[:, [0, 1, 4]], y_train)',
     out:'all 13 MFCCs   accuracy 0.528   95% CI [0.370, 0.680]\nMFCC 1, 2, 5   accuracy 0.750   95% CI [0.589, 0.863]\nMcNemar test   p = 0.039',
     chart:{kind:'bars',title:'Classification accuracy',max:1,ticks:[0,.5,1],fmt:'%',items:[['All 13 MFCCs',.528,.370,.680],['MFCC 1, 2, 5',.75,.589,.8625]]}}
  ];
  var box=document.getElementById('codeP');if(!box)return;
  var tabs=box.querySelector('.snip-tabs'),code=document.getElementById('codeT'),gut=document.getElementById('codeG'),
      out=document.getElementById('codeO'),stat=document.getElementById('codeS'),svg=document.getElementById('codeV'),
      head=document.getElementById('codeH'),cap=document.getElementById('codeC'),run=box.querySelector('.snip-run'),
      tip=document.getElementById('codeTip'),env=document.getElementById('codeEnv'),refEl=document.getElementById('codeRef'),
      btnRun=document.getElementById('codeRun'),btnCopy=document.getElementById('codeCopy'),hover=false,DWELL=9000;
  var RM=matchMedia('(prefers-reduced-motion: reduce)').matches,cur=0,n=0,T=0,vis=false,phase='idle',ICON=window.SNIP_ICONS||{};
  function esc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
  var KW={r:/\b(library|function|TRUE|FALSE|NULL)\b/g,py:/\b(import|from|as|def|return|for|in)\b/g};
  function hl(src,lang){
    return src.split('\n').map(function(line){
      var i=line.indexOf('#'),body=i>=0?line.slice(0,i):line,com=i>=0?line.slice(i):'';
      var parts=body.split(/("[^"]*"?)/);
      body=parts.map(function(p,j){
        if(j%2)return '<span class="t-s">'+esc(p)+'</span>';
        p=esc(p).replace(KW[lang],'<span class="t-k">$1</span>')
          .replace(/(^|[^\w.])(\d+(?:\.\d+)?)\b/g,'$1<span class="t-n">$2</span>')
          .replace(/([A-Za-z_][\w.]*)(?=\()/g,'<span class="t-f">$1</span>')
          .replace(/(&lt;-|\||~|\*)/g,'<span class="t-o">$1</span>')
          .replace(/(\b[a-z_]+)(?=\s=\s)/g,'<span class="t-a">$1</span>');
        return p}).join('');
      return body+(com?'<span class="t-c">'+esc(com)+'</span>':'');
    }).join('\n');
  }
  function cmd(s){return s.lang==='py'?'<span class="t-p">$</span> python '+s.file:'<span class="t-p">&gt;</span> source(<span class="t-s">"'+s.file+'"</span>)'}
  function hlOut(t){return esc(t).replace(/(#.*)$/gm,'<span class="t-c">$1</span>').replace(/(^|[\s\[(=])(-?\d*\.\d+|\d+\.\d+)/g,'$1<span class="t-n">$2</span>')}
  function setStat(s){stat.textContent=s}
  function drawCode(){var s=S[cur],src=s.code.slice(0,n),lines=s.code.split('\n').length,shown=src.split('\n').length;
    code.innerHTML=hl(src,s.lang)+(n<s.code.length?'<span class="t-cur"></span>':'');
    var g='';for(var i=1;i<=lines;i++)g+=(i<=shown?i:'')+'\n';gut.textContent=g}
  // ---------------------------------------------------------------- charts (SVG)
  var NS='http://www.w3.org/2000/svg';
  function el(t,a,txt){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e}
  function fmt(v,f){return f==='%'?Math.round(v*100)+'%':v.toFixed(f||2).replace(/^0\./,'.')}
  function chart(c,anim){
    while(svg.firstChild)svg.removeChild(svg.firstChild);head.textContent=c.title;
    var W=300,L=0,R=W,row=40,top=8,H=top+c.items.length*row+26;svg.setAttribute('viewBox','0 0 '+W+' '+H);
    var x;
    if(c.kind==='bars'){x=function(v){return L+(R-L-34)*v/c.max}}
    else{var a=Math.log(c.lo),b=Math.log(c.hi);x=function(v){return L+8+(R-L-16)*(Math.log(v)-a)/(b-a)}}
    var axisY=top+c.items.length*row+4;
    c.ticks.forEach(function(t){var xx=x(t);svg.appendChild(el('line',{x1:xx,x2:xx,y1:top-4,y2:axisY,class:'g-grid'}));
      svg.appendChild(el('text',{x:xx,y:axisY+14,'text-anchor':'middle',class:'g-tick'},c.kind==='bars'?(c.fmt==='%'?Math.round(t*100)+'%':String(t)):String(t)))});
    if(c.ref){var xr=x(c.ref);svg.appendChild(el('line',{x1:xr,x2:xr,y1:top-4,y2:axisY,class:'g-ref'}))}
    c.items.forEach(function(it,i){
      var y=top+i*row,yc=y+24,g=el('g',{class:'g-item'+(anim?'':' on'),style:'transition-delay:'+(i*160)+'ms','data-i':i});
      g.appendChild(el('rect',{x:0,y:y,width:W,height:row,class:'g-hit'}));
      g.appendChild(el('text',{x:L,y:y+9,class:'g-lab'},it[0]));
      if(c.kind==='bars'){
        var w=x(it[1])-L;g.appendChild(el('rect',{x:L,y:yc-6,width:Math.max(1,w),height:12,class:'g-bar',style:'transform-origin:'+L+'px '+yc+'px'}));
        if(it.length>3){g.appendChild(el('line',{x1:x(it[2]),x2:x(it[3]),y1:yc,y2:yc,class:'g-ci'}));
          [it[2],it[3]].forEach(function(v){g.appendChild(el('line',{x1:x(v),x2:x(v),y1:yc-4,y2:yc+4,class:'g-ci'}))})}
        g.appendChild(el('text',{x:x(it.length>3?it[3]:it[1])+6,y:yc+4,class:'g-val'},fmt(it[1],c.fmt)));
      }else{
        g.appendChild(el('line',{x1:x(it[2]),x2:x(it[3]),y1:yc,y2:yc,class:'g-ci'}));
        g.appendChild(el('rect',{x:x(it[1])-5,y:yc-5,width:10,height:10,class:'g-pt'}));
        var vx=x(it[1]),anchor=vx>W-60?'end':'start';
        g.appendChild(el('text',{x:anchor==='end'?x(it[2])-6:x(it[3])+6,y:yc+4,'text-anchor':anchor,class:'g-val'},String(it[1])));
      }
      svg.appendChild(g)});
    if(anim)requestAnimationFrame(function(){requestAnimationFrame(function(){[].forEach.call(svg.querySelectorAll('.g-item'),function(g){g.classList.add('on')})})});
  }
  // ---------------------------------------------------------------- sequence: type, run, print, plot
  function reset(k){cur=k;clearTimeout(T);cap.textContent=S[k].cap;env.textContent=S[k].env;tip.style.display='none';
    refEl.innerHTML=S[k].doi?'<a href="https://doi.org/'+S[k].doi+'" target="_blank" rel="noopener">'+S[k].ref+' \u2197</a>':S[k].ref;
    box.style.setProperty('--dwell','0ms');box.classList.remove('counting');
    [].forEach.call(tabs.children,function(b,j){b.setAttribute('aria-selected',j===k);b.tabIndex=j===k?0:-1})}
  function complete(k){reset(k);n=S[k].code.length;drawCode();out.innerHTML=cmd(S[k])+'\n'+hlOut(S[k].out);chart(S[k].chart,false);run.classList.add('on');phase='done';setStat('done');
    if(!RM&&vis)dwell()}
  function start(k){reset(k);n=0;out.innerHTML='';run.classList.remove('on');while(svg.firstChild)svg.removeChild(svg.firstChild);head.textContent='';phase='type';setStat('editing');step()}
  function step(){if(!vis)return;var s=S[cur];
    if(phase==='type'){n=Math.min(s.code.length,n+3);drawCode();if(n<s.code.length){T=setTimeout(step,22);return}
      phase='run';setStat('running\u2026');run.classList.add('on');out.innerHTML='';T=setTimeout(step,450);return}
    if(phase==='run'){phase='print';out.innerHTML=cmd(s);out.dataset.i=0;T=setTimeout(step,260);return}
    if(phase==='print'){var L=s.out.split('\n'),i=+out.dataset.i+1;out.innerHTML=cmd(s)+'\n'+hlOut(L.slice(0,i).join('\n'));out.dataset.i=i;
      if(i<L.length){T=setTimeout(step,140);return}
      phase='plot';chart(s.chart,true);setStat('done');phase='done';dwell()}}
  function dwell(){clearTimeout(T);if(hover||RM||!vis)return;box.classList.remove('counting');void box.offsetWidth;
    box.style.setProperty('--dwell',DWELL+'ms');box.classList.add('counting');T=setTimeout(next,DWELL)}
  function next(){if(vis)start((cur+1)%S.length)}
  S.forEach(function(s,k){var b=document.createElement('button');b.type='button';b.setAttribute('role','tab');
    b.innerHTML=(ICON[s.lang]||'')+'<span>'+s.file+'</span>';
    b.addEventListener('click',function(){complete(k)});
    b.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();var j=(k+(e.key==='ArrowRight'?1:S.length-1))%S.length;complete(j);tabs.children[j].focus()}});
    tabs.appendChild(b)});
  complete(0);
  if(!RM){n=0;drawCode();out.innerHTML='';run.classList.remove('on');setStat('');phase='wait'}
  new IntersectionObserver(function(es){var was=vis;vis=es[0].isIntersecting;
    if(vis&&!was&&!RM){clearTimeout(T);if(phase==='wait')start(cur);else if(phase==='done')dwell();else step()}
    if(!vis){clearTimeout(T);box.classList.remove('counting')}},{threshold:.35}).observe(box);
  box.addEventListener('pointerenter',function(){hover=true;if(phase==='done'){clearTimeout(T);box.classList.remove('counting')}});
  box.addEventListener('pointerleave',function(){hover=false;if(phase==='done')dwell()});
  btnRun.addEventListener('click',function(){if(RM){complete(cur);return}vis=true;start(cur)});
  btnCopy.addEventListener('click',function(){var t=S[cur].code,lab=btnCopy.querySelector('span');
    (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){lab.textContent='Copied'},function(){lab.textContent='Select'}).then(function(){setTimeout(function(){lab.textContent='Copy'},1600)})});
  // values on hover
  svg.addEventListener('pointermove',function(e){var g=e.target.closest&&e.target.closest('.g-item');if(!g){tip.style.display='none';return}
    var it=S[cur].chart.items[+g.dataset.i],c=S[cur].chart,r=svg.parentNode.getBoundingClientRect();
    var v=c.fmt==='%'?Math.round(it[1]*1000)/10+'%':String(it[1]),ci=it.length>3?(c.fmt==='%'?' ['+Math.round(it[2]*1000)/10+'%, '+Math.round(it[3]*1000)/10+'%]':' ['+it[2]+', '+it[3]+']'):'';
    tip.innerHTML='<b>'+it[0]+'</b>'+v+(ci?' <span>95% CI'+ci+'</span>':'');tip.style.display='block';
    var x=e.clientX-r.left+12,y=e.clientY-r.top+12;if(x+tip.offsetWidth>r.width)x=e.clientX-r.left-tip.offsetWidth-12;tip.style.left=x+'px';tip.style.top=y+'px'});
  svg.addEventListener('pointerleave',function(){tip.style.display='none'});
})();
