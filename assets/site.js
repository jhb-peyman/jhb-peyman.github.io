(function(){
  var d=document,de=d.documentElement,mq=matchMedia('(prefers-color-scheme: dark)');

  // ---------------- light / dark: follows the system until the visitor chooses
  var btn=d.getElementById('theme');
  function isDark(){var t=de.dataset.theme;return t?t==='dark':mq.matches}
  function paint(){if(btn)btn.setAttribute('aria-label',isDark()?'Switch to light mode':'Switch to dark mode')}
  function changed(){paint();d.dispatchEvent(new Event('themechange'))}
  if(btn)btn.addEventListener('click',function(){
    var t=isDark()?'light':'dark';de.dataset.theme=t;try{localStorage.setItem('pj-theme',t)}catch(e){}changed();
  });
  if(mq.addEventListener)mq.addEventListener('change',function(){if(!de.dataset.theme)changed()});
  paint();

  // ---------------- publication filters
  var pubs=d.querySelectorAll('.pub[data-status]');
  if(pubs.length){
    var st='all',tp='all',count=d.getElementById('count');
    function apply(){
      var n=0;
      pubs.forEach(function(p){
        var ok=(st==='all'||p.dataset.status===st)&&(tp==='all'||(' '+p.dataset.topics+' ').indexOf(' '+tp+' ')>=0);
        p.classList.toggle('hidden',!ok);if(ok)n++;
      });
      d.querySelectorAll('.yr').forEach(function(y){y.classList.toggle('hidden',!y.querySelector('.pub:not(.hidden)'))});
      if(count)count.textContent=n===pubs.length?'Showing all '+n+' items.':'Showing '+n+' of '+pubs.length+' items.';
    }
    d.querySelectorAll('.frow').forEach(function(row){
      row.addEventListener('click',function(e){
        var b=e.target.closest('button');if(!b)return;
        row.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
        if(row.dataset.f==='status')st=b.dataset.v;else tp=b.dataset.v;apply();
      });
    });
    apply();
  }

  // ---------------- citations (same APA 7 and BibTeX rules as the live site)
  var CITES={};try{CITES=JSON.parse(d.getElementById('cites').textContent)}catch(e){}
  var live=d.getElementById('live');
  function initials(first){
    return first.split(/\s+/).filter(function(t){return t&&t.indexOf('/')<0}).map(function(t){
      return t.split('-').map(function(x){return x.charAt(0).toUpperCase()+'.'}).join('-');
    }).join(' ');
  }
  function apaAuthors(a){
    var l=a.map(function(p){return p[0]+', '+initials(p[1])});
    return l.length<2?l[0]:l.length===2?l[0]+', & '+l[1]:l.slice(0,-1).join(', ')+', & '+l[l.length-1];
  }
  var DEPT='Department of Curriculum & Teaching, University of Kansas';
  function apa(r){
    var it=function(x){return '<i>'+x+'</i>'},au=apaAuthors(r.a),s;
    if(r.kind==='article'){
      s=au+' ('+r.y+'). '+r.t+'. '+it(r.v);
      if(r.vol)s+=', '+it(r.vol)+(r.iss?'('+r.iss+')':'');
      if(r.pp)s+=', '+r.pp.replace('-','\u2013');
      if(r.art)s+=', Article '+r.art;
      s+='.';
      if(r.online)s+=' Advance online publication.';
    }else if(r.kind==='submitted'){
      s=au+' ('+r.y+'). '+it(r.t)+' [Manuscript submitted for publication]. '+DEPT+'.';
    }else if(r.kind==='talk'){
      s=au+' ('+r.y+', '+r.date+'). '+it(r.t)+' ['+r.fmt+']. '+r.v+', '+r.loc+'.';
    }else{
      s=au+' ('+r.y+'). '+it(r.t)+'. '+r.v+'.';
    }
    var link=r.doi?'https://doi.org/'+r.doi:(r.url||'');
    if(link)s+=' '+link;
    return {html:s.replace(/&/g,'&amp;'),text:s.replace(/<[^>]+>/g,'')};
  }
  var ACC={'á':"{\\'a}",'é':"{\\'e}",'í':"{\\'i}",'ó':"{\\'o}",'ú':"{\\'u}",'ñ':'{\\~n}'};
  function tex(s){return s.replace(/&/g,'\\&').replace(/"([^"]*)"/g,"``$1''").replace(/[áéíóúñ]/g,function(c){return ACC[c]})}
  function bibtex(r){
    var au=r.a.map(function(p){return tex(p[0])+', '+tex(p[1])}).join(' and '),f=['author = {'+au+'}','title = {{'+tex(r.t)+'}}'],type='article';
    if(r.kind==='article'){
      f.push('journal = {'+tex(r.v)+'}','year = {'+r.y+'}');
      if(r.vol)f.push('volume = {'+r.vol+'}');
      if(r.iss)f.push('number = {'+r.iss+'}');
      if(r.pp)f.push('pages = {'+r.pp.replace('-','--')+'}');
      if(r.art)f.push('eid = {'+r.art+'}');
      if(r.online)f.push('note = {Advance online publication}');
    }else if(r.kind==='submitted'){
      type='unpublished';f.push('note = {Manuscript submitted for publication}','year = {'+r.y+'}');
    }else if(r.kind==='talk'){
      type='inproceedings';f.push('booktitle = {'+tex(r.bt)+'}','year = {'+r.y+'}','month = '+r.month,'address = {Los Angeles, CA}','note = {Paper presented at the '+tex(r.v)+', '+r.date+', '+r.y+'}');
    }else{
      type='misc';f.push('year = {'+r.y+'}');
      if(r.kind==='preprint')f.push('howpublished = {'+tex(r.v)+'}');else f.push('note = {Reproducible research artifact}');
      if(r.eprint)f.push('eprint = {'+r.eprint+'}','archivePrefix = {arXiv}');
    }
    if(r.doi)f.push('doi = {'+r.doi+'}');else if(r.url)f.push('url = {'+r.url+'}');
    return '@'+type+'{'+r.key+',\n  '+f.join(',\n  ')+'\n}';
  }
  function copyText(t){
    if(navigator.clipboard&&navigator.clipboard.writeText)return navigator.clipboard.writeText(t);
    return new Promise(function(res,rej){
      var ta=d.createElement('textarea');ta.value=t;ta.style.cssText='position:fixed;opacity:0';d.body.appendChild(ta);ta.select();
      try{d.execCommand('copy')?res():rej()}catch(e){rej(e)}ta.remove();
    });
  }
  function copyRich(html,text){
    if(navigator.clipboard&&window.ClipboardItem){
      return navigator.clipboard.write([new ClipboardItem({'text/html':new Blob(['<p style="margin:0 0 0 0.5in;text-indent:-0.5in">'+html+'</p>'],{type:'text/html'}),'text/plain':new Blob([text],{type:'text/plain'})})]).catch(function(){return copyText(text)});
    }
    return copyText(text);
  }
  d.querySelectorAll('[data-cite]').forEach(function(box){
    var r=CITES[box.dataset.cite];if(!r)return;
    [['Copy APA','apa'],['BibTeX','bib']].forEach(function(spec){
      var b=d.createElement('button');b.type='button';b.textContent=spec[0];
      b.setAttribute('aria-label',spec[1]==='apa'?'Copy APA citation':'Copy BibTeX entry');
      b.addEventListener('click',function(){
        var job=spec[1]==='apa'?(function(){var c=apa(r);return copyRich(c.html,c.text)})():copyText(bibtex(r));
        job.then(function(){
          b.classList.add('ok');b.textContent='Copied';if(live)live.textContent=(spec[1]==='apa'?'APA citation':'BibTeX entry')+' copied';
          setTimeout(function(){b.classList.remove('ok');b.textContent=spec[0]},1800);
        },function(){b.textContent='Press Ctrl+C';setTimeout(function(){b.textContent=spec[0]},1800)});
      });
      box.appendChild(b);
    });
  });
})();
