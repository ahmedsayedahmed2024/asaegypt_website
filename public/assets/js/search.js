/* ASA site search: one engine for the header search (every page), the search page (/search/, /ar/search/) and the
   in-article finder of the reference guide (guide.js, through window.ASASearch).
   The index (assets/search/<lang>.json) is built by src/search.py from the rendered pages: one record per passage
   (paragraph, list item, table row, card, callout, FAQ item), with the passage's id in the page. It is loaded the first
   time a search box gets focus. A result opens the page at the passage: <url>?hl=<query>#<id>; on arrival the passage
   is revealed, scrolled into view and its matching words are highlighted for a few seconds.
   Everything runs in the browser: no external service, no tracking, no CDN. */
(function(){
  'use strict';
  var panel=document.getElementById('site-search');
  if(!panel)return;
  var cfg=JSON.parse(panel.getAttribute('data-cfg')),S=cfg.s;
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  var MIN_CHARS=2,DROP_PAGES=6,PER_PAGE=2,SNIP=140;
  var store=function(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}};

  // ---------- normalisation (index and query) ----------
  // lower case; Latin accents off; Arabic: no diacritics or tatweel, one form of alef, yaa, taa marbuta/haa, waw and
  // yaa with hamza; Arabic digits as 0-9; an Arabic letter stuck to a Latin one ("وACA") becomes two words
  var AR={'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي'};
  var MARKS=/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
  var WORD=/[\p{L}\p{N}]+/gu;                    // a word in normalised text
  var OWORD=/[\p{L}\p{N}\p{M}ـ]+/gu;        // a word in the original text (keeps Arabic marks inside the word)
  function norm(s){
    return String(s).toLowerCase().replace(MARKS,'')
      .replace(/[أإآٱىةؤئ]/g,function(c){return AR[c]})
      .replace(/[٠-٩]/g,function(d){return String.fromCharCode(d.charCodeAt(0)-0x0630)})
      .replace(/[۰-۹]/g,function(d){return String.fromCharCode(d.charCodeAt(0)-0x06C0)})
      .normalize('NFKD').replace(/[̀-ͯ]/g,'')
      .replace(/([ء-ي])(?=[a-z0-9])/g,'$1 ').replace(/([a-z0-9])(?=[ء-ي])/g,'$1 ');
  }
  function words(s){return norm(s).match(WORD)||[]}
  var isAr=function(w){return /[ء-ي]/.test(w)};
  var isNum=function(w){return /^\d+$/.test(w)};
  // Arabic: a word also stands without «ال» (and و/ف/ب/ك + «ال», «لل»), or without a leading و/ف/ب/ل
  function variants(w){
    var out=[w];
    if(isAr(w)){
      var m=w.match(/^(?:[وفبك]?ال|لل)(..+)$/);
      if(m)out.push(m[1]);
      else if(w.length>=4&&/^[وفبل]/.test(w))out.push(w.slice(1));
    }
    return out;
  }
  function stem(w){var m=isAr(w)&&w.match(/^(?:[وفبك]?ال|لل)(..+)$/);return m?m[1]:w}
  // small words that do not need to match ("of", «في») when the query has other words
  var STOP=new Set(['of','and','the','a','an','in','on','for','to','by','with','at','or','from','is','are','its',
    'في','من','على','الى','عن','او','مع','ان','هل','ما','لا','تم','هو','هي','ذلك','التي','الذي']);
  function keep(ws){
    var long=ws.filter(function(w){return w.length>1||isNum(w)});
    if(!long.length)return ws.filter(function(w){return !isAr(w)});
    var main=long.filter(function(w){return !STOP.has(w)});
    return main.length?main:long;
  }
  function phrase(s){return keep(words(s).map(stem)).join(' ')}
  // query → terms (single letters dropped, except digits; a lone Arabic «و» goes too; small words dropped)
  function terms(q){return keep(words(q).map(stem))}
  // words typed in capitals ("FRA", "CA", "IQEX") are acronyms: in the text they must match exactly, not as the start
  // of a longer word ("framework", "fraud"); acronyms and names of institutions still match their beginning
  function caps(q){
    var out=new Set();
    (String(q).match(/[A-Za-z0-9&]+/g)||[]).forEach(function(w){if(w.length>=2&&/[A-Z]/.test(w)&&w===w.toUpperCase())out.add(norm(w))});
    return out;
  }
  // Arabic "skeleton": «ضريبة», «ضريبي» and «الضرائب» meet (drop a common ending, then the long vowels)
  function skel(w){
    var t=w.replace(/(?:ات|ون|ين|ان|يه|ه)$/,'');
    if(t.length<3)t=w;
    return t.charAt(0)+t.slice(1).replace(/[اوي]/g,'');
  }
  // optimal string alignment distance, stops early above max
  function dist(a,b,max){
    if(Math.abs(a.length-b.length)>max)return max+1;
    var d=[],i,j;
    for(i=0;i<=a.length;i++){d[i]=[i]}
    for(j=1;j<=b.length;j++)d[0][j]=j;
    for(i=1;i<=a.length;i++){
      var low=max+1;
      for(j=1;j<=b.length;j++){
        var c=a[i-1]===b[j-1]?0:1;
        d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+c);
        if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])d[i][j]=Math.min(d[i][j],d[i-2][j-2]+1);
        if(d[i][j]<low)low=d[i][j];
      }
      if(low>max)return max+1;
    }
    return d[a.length][b.length];
  }
  // how well an index word w matches a query term t: 1 exact, .8 prefix (3+ letters), .6 one wrong letter (5+ letters),
  // .5 the same Arabic skeleton, .3 prefix of a 2-letter term (only counts in acronyms and names, in the finder)
  function quality(t,w){
    if(w===t)return 1;
    if(isNum(t))return 0;
    var pre=w.lastIndexOf(t,0)===0;
    if(pre)return t.length>=3?.8:.3;
    var ar=isAr(t);
    if(ar!==isAr(w))return 0;
    if(t.length>=5&&w.length>=4&&dist(t,w,1)<=1)return .6;
    if(ar&&t.length>=4){var a=skel(t),b=skel(w);if(a.length>=3&&(a===b||(a.length>=4&&b.lastIndexOf(a,0)===0)))return .5}
    if(!ar&&t.length>=6&&w.length>t.length&&dist(t,w.slice(0,t.length),1)<=1)return .5;
    return 0;
  }

  // ---------- index ----------
  var loaded={};
  function load(lang){
    if(!loaded[lang]){
      var url=lang===cfg.lang?cfg.idx:cfg.idx2;
      loaded[lang]=fetch(url+'?v='+cfg.v).then(function(r){if(!r.ok)throw new Error(r.status);return r.json()}).then(function(j){return prepare(lang,j)});
      loaded[lang].catch(function(){delete loaded[lang]});
    }
    return loaded[lang];
  }
  function post(map,vocab,text,i){
    (norm(text).match(WORD)||[]).forEach(function(w){
      if(w.length<2&&!isNum(w))return;
      variants(w).forEach(function(v){var a=map.get(v);if(!a)map.set(v,a=[]);if(a[a.length-1]!==i)a.push(i);vocab.add(v)});
    });
  }
  function prepare(lang,j){
    var X={lang:lang,pages:[],crumbs:[],ps:[],pw:new Map(),kw:new Map(),cw:new Map(),tw:new Map(),vocab:new Set(),cache:new Map()};
    j.pages.forEach(function(p,i){X.pages.push({i:i,u:p[0],t:p[1],g:p[2],d:p[3],first:-1});post(X.tw,X.vocab,p[1],i)});
    j.h.forEach(function(h,i){X.crumbs.push({s:h,ps:[]});post(X.cw,X.vocab,h,i)});
    j.p.forEach(function(r,i){
      var P={i:i,pi:r[0],id:r[1],t:r[2],ci:r[3],acr:[],names:[],ents:[]};
      if(r[4])r[4].split(';').forEach(function(e){
        var f=e.split('|');P.ents.push({a:f[0],c:f[1],n:f[2],m:f[3]});P.acr.push(phrase(f[0]));post(X.kw,X.vocab,f[0],i);
        [f[2],f[3]].forEach(function(n){if(n){P.names.push(phrase(n));post(X.kw,X.vocab,n,i)}});
      });
      P.lead=new Set();(norm(P.t).match(WORD)||[]).slice(0,3).forEach(function(w){variants(w).forEach(function(v){P.lead.add(v)})});
      X.crumbs[P.ci].ps.push(i);
      if(X.pages[P.pi].first<0)X.pages[P.pi].first=i;
      post(X.pw,X.vocab,P.t,i);
      X.ps.push(P);
    });
    // aliases (data/search_aliases.yml + the institution registry): designations ("CA" → ICAS, CA ANZ…) and synonyms
    var des=new Map(),groups=[],syn=new Map(),raw=[];
    Object.keys(j.al.d).forEach(function(k){
      raw.push(k);
      des.set(phrase(k),j.al.d[k].map(function(t,n){return {to:phrase(t[0]),also:!!t[1],en:t[2],ar:t[3],n:n}}));
    });
    j.al.s.forEach(function(g,gi){
      var m=g.map(phrase).filter(Boolean);groups.push(m);
      g.forEach(function(x){raw.push(x)});
      m.forEach(function(x){var a=syn.get(x);if(!a)syn.set(x,a=[]);if(a.indexOf(gi)<0)a.push(gi)});
    });
    X.al={des:des,groups:groups,syn:syn,raw:raw};
    return X;
  }

  // the query and its alternatives: the designations of the whole query, and each phrase replaced by its synonyms
  function alternatives(q,al){
    var ts=terms(q);if(!ts.length)return [];
    var cp=caps(q),out=[{ts:ts,w:1,also:false,order:0,exact:cp}],seen={};seen[ts.join(' ')]=1;
    function add(v){var k=v.ts.join(' ');if(!seen[k]&&out.length<24){seen[k]=1;out.push(v)}}
    var d=al.des.get(ts.join(' '));
    if(d)d.forEach(function(t){
      if(t.to===ts[0]&&ts.length===1)out[0].label=t[cfg.lang];   // "CMA" is also an acronym: label its own card too
      add({ts:t.to.split(' '),w:.95,also:t.also,label:t[cfg.lang],order:t.n+1,alias:1,exact:new Set(t.to.split(' '))});
    });
    for(var len=ts.length;len>=1;len--)for(var st=0;st+len<=ts.length;st++){
      var span=ts.slice(st,st+len).join(' '),gs=al.syn.get(span);if(!gs)continue;
      gs.forEach(function(gi){al.groups[gi].forEach(function(m){
        if(m!==span)add({ts:ts.slice(0,st).concat(m.split(' '),ts.slice(st+len)),w:.9,also:false,order:0,syn:1,exact:cp});
      })});
    }
    return out;
  }
  function matchTerm(t,X){
    var m=X.cache.get(t);if(m)return m;
    m=new Map();X.vocab.forEach(function(w){var q=quality(t,w);if(q)m.set(w,q)});
    X.cache.set(t,m);return m;
  }
  function collect(map,m,min){
    var out=new Map();
    m.forEach(function(q,w){if(q<min)return;var a=map.get(w);if(a)for(var n=0;n<a.length;n++){if((out.get(a[n])||0)<q)out.set(a[n],q)}});
    return out;
  }
  // search one index. opt.page: only this page (the in-article finder); opt.finder: names that start with the
  // query also rank as institutions. Returns {pages:[{p, score, hits:[{P, score, v}]}]}, best page first.
  function run(q,X,opt){
    opt=opt||{};
    var vs=alternatives(q,X.al),best=new Map(),titleOnly=new Map();
    vs.forEach(function(v){
      v.words=new Set();
      var tm=v.ts.map(function(t){
        var m=matchTerm(t,X),min=v.exact.has(t)?1:v.syn?.8:.5;   // synonyms: whole words or their beginning, no typos
        m.forEach(function(qq,w){if(qq>=min)v.words.add(w)});
        return {m:m,min:min,p:collect(X.pw,m,min),k:collect(X.kw,m,opt.finder?0:.5),c:collect(X.cw,m,min),t:collect(X.tw,m,min)};
      });
      var cand=new Set();
      tm[0].p.forEach(function(_,i){cand.add(i)});tm[0].k.forEach(function(_,i){cand.add(i)});
      tm[0].c.forEach(function(_,ci){X.crumbs[ci].ps.forEach(function(i){cand.add(i)})});
      var vstr=v.ts.join(' ');
      cand.forEach(function(i){
        var P=X.ps[i],pg=X.pages[P.pi];
        if(opt.page&&pg.u!==opt.page)return;
        // per word: how exact the best match is (1000 × quality), then where it is: page title (300) > section
        // heading or the institution's keys (200) > passage text (100); averaged over the words of the query
        var sum=0;
        for(var n=0;n<tm.length;n++){
          var a=tm[n],qp=a.p.get(i)||0,qk=a.k.get(i)||0,qc=a.c.get(P.ci)||0,qi=Math.max(qp,qk,qc);
          if(!qi)return;                                        // every word must be in the passage, its heading or its keys
          var lead=0;if(qp)P.lead.forEach(function(w){var x=a.m.get(w)||0;if(x>=a.min&&x>lead)lead=x});
          sum+=qi*1000+qp*100+qk*200+qc*200+(a.t.get(P.pi)||0)*300+lead*100;  // a passage that starts with the word (a label, a term) counts a little more
        }
        sum/=tm.length;
        var tier=0;
        if(P.acr.indexOf(vstr)>=0||P.names.indexOf(vstr)>=0)tier=v.also?2:3;   // the institution's own card or row
        else if(opt.finder&&P.ents.length&&tm.every(function(a){return a.k.has(i)}))tier=1;
        var sc=tier>=2?tier*10000+100-v.order:tier*10000+sum*v.w;
        var b=best.get(i);if(!b||b.score<sc)best.set(i,{P:P,score:sc,v:v,label:tier>=2?v.label:''});
      });
      if(!opt.page){                                           // pages whose title alone matches
        var ok=null;
        tm.forEach(function(a){var s=new Map();a.t.forEach(function(qq,pi){s.set(pi,qq)});
          if(!ok){ok=s;return}var nx=new Map();ok.forEach(function(x,pi){if(s.has(pi))nx.set(pi,x+s.get(pi))});ok=nx});
        if(ok)ok.forEach(function(x,pi){var sc=x*1300/tm.length*v.w;if((titleOnly.get(pi)||{score:0}).score<sc)titleOnly.set(pi,{score:sc,v:v})});
      }
    });
    var byPage=new Map();
    best.forEach(function(h){var g=byPage.get(h.P.pi);if(!g)byPage.set(h.P.pi,g={p:X.pages[h.P.pi],X:X,score:0,hits:[]});g.hits.push(h);if(h.score>g.score)g.score=h.score});
    titleOnly.forEach(function(t,pi){
      if(byPage.has(pi)||X.pages[pi].first<0)return;
      byPage.set(pi,{p:X.pages[pi],X:X,score:t.score,hits:[{P:X.ps[X.pages[pi].first],score:t.score,v:t.v,top:1}]});
    });
    var pages=[];
    byPage.forEach(function(g){g.hits.sort(function(a,b){return b.score-a.score||a.P.i-b.P.i});pages.push(g)});
    pages.sort(function(a,b){return b.score-a.score||(b.p.d||'').localeCompare(a.p.d||'')||a.p.i-b.p.i});
    return {pages:pages,n:pages.reduce(function(s,g){return s+g.hits.length},0)};
  }
  // "Did you mean": the closest alias or page title, or each word replaced by the closest word of the index
  function suggest(q,X){
    var qn=terms(q).join(' ');if(!qn)return '';
    var max=qn.length<=4?1:2,bestD=max+1,bestS='';
    X.al.raw.concat(X.pages.map(function(p){return p.t})).forEach(function(c){
      var cn=phrase(c);if(!cn||cn===qn)return;
      var d=dist(qn,cn,max);if(d<bestD){bestD=d;bestS=c}
    });
    if(bestS)return bestS;
    var changed=false,out=terms(q).map(function(t){
      if(X.vocab.has(t)||t.length<4)return t;
      var bd=3,bw=t;X.vocab.forEach(function(w){if(Math.abs(w.length-t.length)>2)return;var d=dist(t,w,2);if(d<bd){bd=d;bw=w}});
      if(bw!==t)changed=true;return bw;
    });
    return changed?out.join(' '):'';
  }

  // ---------- text helpers ----------
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function isHit(word,set){var ws=words(word);for(var n=0;n<ws.length;n++){var vs=variants(ws[n]);for(var k=0;k<vs.length;k++)if(set.has(vs[k]))return true}return false}
  function hl(text,set){
    var out='',last=0;
    text.replace(OWORD,function(w,i){out+=esc(text.slice(last,i))+(set&&isHit(w,set)?'<mark>'+esc(w)+'</mark>':esc(w));last=i+w.length});
    return out+esc(text.slice(last));
  }
  function snippet(text,set,len){
    len=len||SNIP;
    var at=-1;text.replace(OWORD,function(w,i){if(at<0&&set&&isHit(w,set))at=i});
    if(text.length<=len)return hl(text,set);
    var start=at<0?0:Math.max(0,at-Math.round(len*.35));
    if(start>0){var sp=text.indexOf(' ',start);start=sp<0||sp>at?start:sp+1}
    var piece=text.slice(start,start+len);
    if(start+len<text.length)piece=piece.replace(/\s+\S*$/,'');
    return (start>0?'…':'')+hl(piece,set)+(start+piece.length<text.length?'…':'');
  }
  function date(iso){if(!iso)return '';var p=iso.split('-');return (+p[2])+' '+cfg.months[+p[1]-1]+' '+p[0]}
  function href(u,q,id){return u+'?hl='+encodeURIComponent(q)+(id?'#'+encodeURIComponent(id):'')}

  // ---------- results (header panel and search page) ----------
  var ALSO_KEY='asaSearchAlso';
  function alsoOn(){return store(ALSO_KEY)==='1'}
  function indexes(){return Promise.all(alsoOn()?[load(cfg.lang),load(cfg.other)]:[load(cfg.lang)])}
  function searchAll(q,idx){
    var pages=[],n=0;
    idx.forEach(function(X){var r=run(q,X);n+=r.n;pages=pages.concat(r.pages)});
    pages.sort(function(a,b){return b.score-a.score||(b.p.d||'').localeCompare(a.p.d||'')||(a.X.lang===cfg.lang?0:1)-(b.X.lang===cfg.lang?0:1)});
    return {pages:pages,n:n};
  }
  var oid=0;
  function hitHtml(g,h,q,opt){
    var X=g.X,other=X.lang!==cfg.lang,la=other?' lang="'+X.lang+'" dir="'+(X.lang==='ar'?'rtl':'ltr')+'"':'';
    var crumb=h.top?S.top:X.crumbs[h.P.ci].s;
    return '<a class="sp-item" href="'+esc(href(g.p.u,q,h.top?'':h.P.id))+'"'+(opt?' id="sp-o'+(oid++)+'" role="option" aria-selected="false"':'')+'>'+
      (crumb?'<span class="sp-crumb"'+la+'>'+esc(crumb)+'</span>':'')+
      '<span class="sp-s"'+la+'>'+snippet(h.P.t,h.v.words)+'</span>'+
      (h.label?'<span class="sp-alias">'+esc(h.label)+'</span>':'')+'</a>';
  }
  function pagesHtml(res,q,maxPages,opt){
    var html='';oid=opt?oid:0;
    res.pages.slice(0,maxPages||res.pages.length).forEach(function(g,k){
      var X=g.X,other=X.lang!==cfg.lang,la=other?' lang="'+X.lang+'" dir="'+(X.lang==='ar'?'rtl':'ltr')+'"':'';
      var meta=[date(g.p.d)].filter(Boolean);if(other)meta.push('<span class="sp-lang">'+esc(S.other)+'</span>');
      html+='<div class="sp-page" role="group" aria-label="'+esc(g.p.t)+'">'+
        '<p class="sp-ph"><span class="sp-badge sp-b-'+g.p.g+'"'+(g.p.g==='next'?' dir="ltr" lang="en"':'')+'>'+esc(S.types[g.p.g]||g.p.g)+'</span>'+
        '<a class="sp-pt" tabindex="-1" href="'+esc(href(g.p.u,q,''))+'"'+la+'>'+hl(g.p.t,g.hits[0].v.words)+'</a>'+
        (meta.length?'<span class="sp-meta">'+meta.join(' · ')+'</span>':'')+'</p>';
      g.hits.slice(0,PER_PAGE).forEach(function(h){html+=hitHtml(g,h,q,opt)});
      if(g.hits.length>PER_PAGE){
        html+='<button type="button" class="sp-more"'+(opt?' id="sp-o'+(oid++)+'" role="option" aria-selected="false"':'')+' aria-expanded="false">'+
          '<span>'+esc(S.matches.replace('{n}',g.hits.length))+'</span><b>'+esc(S.show_all)+'</b></button><div class="sp-rest" hidden>';
        g.hits.slice(PER_PAGE).forEach(function(h){html+=hitHtml(g,h,q,opt)});
        html+='</div>';
      }
      html+='</div>';
    });
    return html;
  }
  function emptyHtml(q,X,X2,opt){
    var html='<div class="sp-empty"><p class="sp-none">'+esc(S.none)+' <b>«'+esc(q)+'»</b></p>';
    var s=X?suggest(q,X):'';
    if(s)html+='<p class="sp-dym">'+esc(S.dym)+' <a class="sp-sugg-q" href="'+esc(cfg.page+'?q='+encodeURIComponent(s))+'" data-q="'+esc(s)+'"'+(opt?' id="sp-o'+(oid++)+'" role="option" aria-selected="false"':'')+'>'+esc(s)+'</a>'+(cfg.lang==='ar'?'؟':'?')+'</p>';
    if(X2){var r2=run(q,X2);if(r2.n)html+='<p class="sp-other"><a href="'+esc(cfg.page2+'?q='+encodeURIComponent(q))+'" lang="'+S.other_res_lang+'" dir="'+(S.other_res_lang==='ar'?'rtl':'ltr')+'"'+(opt?' id="sp-o'+(oid++)+'" role="option" aria-selected="false"':'')+'>'+esc(S.other_res.replace('{n}',r2.n))+'</a></p>'}
    html+='<p class="sp-try">'+esc(S.try_)+'</p><ul>'+
      cfg.links.map(function(l){return '<li><a class="sp-sugg" href="'+esc(l[1])+'"'+(opt?' id="sp-o'+(oid++)+'" role="option" aria-selected="false"':'')+'>'+esc(l[0])+'</a></li>'}).join('')+'</ul></div>';
    return html;
  }
  function wireResults(box,onSuggest){
    box.addEventListener('click',function(e){
      var more=e.target.closest('.sp-more');
      if(more){var rest=more.nextElementSibling,open=more.getAttribute('aria-expanded')!=='true';rest.hidden=!open;more.setAttribute('aria-expanded',open);more.querySelector('b').textContent=open?S.show_less:S.show_all;return}
      var sg=e.target.closest('.sp-sugg-q');
      if(sg&&onSuggest){e.preventDefault();onSuggest(sg.getAttribute('data-q'));return}
      var a=e.target.closest('a.sp-item,a.sp-pt');
      if(a&&samePage(a)){e.preventDefault();openHere(a)}
    });
  }
  function samePage(a){return a.pathname===location.pathname&&a.host===location.host}
  function openHere(a){
    var p=new URLSearchParams(a.search),q=p.get('hl')||'',id=decodeURIComponent(a.hash.slice(1));
    close();
    try{history.replaceState(history.state,'',location.pathname+(id?'#'+id:''))}catch(e){}
    go(q,id);
  }
  function one(s){return cfg.lang==='en'?s.replace(/\b1 matches\b/,'1 match').replace(/\b1 pages\b/,'1 page'):s}
  function count(res){return one(S.summary.replace('{n}',res.n).replace('{p}',res.pages.length))}

  // ---------- header panel ----------
  var header=document.querySelector('.site-header'),scrim=document.querySelector('.search-scrim');
  var input=panel.querySelector('.sp-input'),box=panel.querySelector('.sp-results'),status=panel.querySelector('.sp-status');
  var openers=document.querySelectorAll('[data-open-search]'),back=null,active=-1,seq=0;
  function isOpen(){return !panel.hidden}
  function open(){
    if(isOpen()){input.focus();return}
    back=document.activeElement;
    panel.hidden=false;scrim.hidden=false;
    header.classList.add('search-open','solid');document.body.classList.add('search-lock');
    openers.forEach(function(b){b.setAttribute('aria-expanded','true')});
    input.focus();input.select();
    runPanel();
  }
  function close(){
    if(!isOpen())return;
    panel.hidden=true;scrim.hidden=true;
    header.classList.remove('search-open');document.body.classList.remove('search-lock');
    window.dispatchEvent(new Event('scroll'));                                // header colour back to normal
    openers.forEach(function(b){b.setAttribute('aria-expanded','false')});
    if(back&&back.focus&&document.contains(back))back.focus();
  }
  function options(){return [].filter.call(box.querySelectorAll('[role="option"]'),function(o){return !o.closest('[hidden]')})}
  function setActive(i){
    var os=options();active=os.length?(i+os.length)%os.length:-1;
    os.forEach(function(o,j){o.setAttribute('aria-selected',j===active);o.classList.toggle('on',j===active)});
    if(active>=0){input.setAttribute('aria-activedescendant',os[active].id);os[active].scrollIntoView({block:'nearest'})}
    else input.removeAttribute('aria-activedescendant');
  }
  function runPanel(){
    var q=input.value.trim(),my=++seq;
    active=-1;input.removeAttribute('aria-activedescendant');
    if(q.length<MIN_CHARS){box.innerHTML='<p class="sp-hint">'+esc(S.hint)+'</p>';input.setAttribute('aria-expanded','false');status.textContent='';return}
    if(!box.querySelector('.sp-page,.sp-empty'))box.innerHTML='<p class="sp-hint">'+esc(S.loading)+'</p>';
    indexes().then(function(idx){
      if(my!==seq)return;
      var res=searchAll(q,idx);oid=0;
      if(!res.pages.length){
        (alsoOn()?Promise.resolve(null):load(cfg.other).catch(function(){return null})).then(function(X2){
          if(my!==seq)return;
          box.innerHTML=emptyHtml(q,idx[0],X2,true);status.textContent=S.none+' «'+q+'»';input.setAttribute('aria-expanded','true');
        });
        return;
      }
      box.innerHTML=pagesHtml(res,q,DROP_PAGES,true)+'<a class="sp-all" id="sp-o'+(oid++)+'" role="option" aria-selected="false" href="'+esc(cfg.page+'?q='+encodeURIComponent(q))+'">'+esc(S.all)+' ('+res.pages.length+') <span aria-hidden="true">'+(cfg.lang==='ar'?'←':'→')+'</span></a>';
      status.textContent=count(res);
      input.setAttribute('aria-expanded','true');
    }).catch(function(){if(my===seq)box.innerHTML=emptyHtml(q,null,null,true)});
  }
  var timer;
  input.addEventListener('input',function(){clearTimeout(timer);timer=setTimeout(runPanel,90)});
  input.addEventListener('focus',function(){load(cfg.lang)});
  input.addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();var n=options().length;if(!n)return;setActive(active<0?(e.key==='ArrowDown'?0:n-1):active+(e.key==='ArrowDown'?1:-1))}
    else if(e.key==='Enter'){var os=options();if(active>=0&&os[active]){e.preventDefault();var o=os[active];
      if(o.tagName==='BUTTON'){o.click();setActive(active)}else o.click()}}
  });
  wireResults(box,function(s){input.value=s;runPanel();input.focus()});
  panel.querySelector('.sp-form').addEventListener('submit',function(e){if(input.value.trim().length<MIN_CHARS)e.preventDefault()});
  openers.forEach(function(b){b.addEventListener('click',function(){isOpen()?close():open()})});
  document.querySelectorAll('[data-close-search]').forEach(function(b){b.addEventListener('click',close)});
  document.addEventListener('mousedown',function(e){if(isOpen()&&!panel.contains(e.target)&&!e.target.closest('[data-open-search]'))close()});
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'&&isOpen()){e.preventDefault();close();return}
    var t=e.target,typing=t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if((e.key==='k'||e.key==='K')&&(e.ctrlKey||e.metaKey)&&!e.altKey){e.preventDefault();open();return}
    if(e.key==='/'&&!typing&&!e.ctrlKey&&!e.metaKey&&!e.altKey){e.preventDefault();open()}
  });

  // ---------- "also search the other language" switch (remembered in this browser) ----------
  function wireAlso(btn,again){
    if(!btn)return;btn.hidden=false;btn.setAttribute('aria-checked',alsoOn());
    btn.addEventListener('click',function(){var on=btn.getAttribute('aria-checked')!=='true';store(ALSO_KEY,on?'1':'0');
      document.querySelectorAll('.sp-also').forEach(function(b){b.setAttribute('aria-checked',on)});again()});
  }
  var page=document.querySelector('[data-search-page]'),runPage=function(){};
  wireAlso(panel.querySelector('.sp-also'),function(){if(isOpen())runPanel();if(page)runPage()});

  // ---------- search page (/search/?q=...) ----------
  if(page){
    var pin=page.querySelector('.sp-input'),pbox=page.querySelector('.sp-results'),pcount=page.querySelector('.sp-count'),pseq=0;
    runPage=function(){
      var q=pin.value.trim(),my=++pseq;
      try{history.replaceState(null,'',q?cfg.page+'?q='+encodeURIComponent(q):cfg.page)}catch(e){}
      if(q.length<MIN_CHARS){pbox.innerHTML=q?'<p class="sp-hint">'+esc(S.hint)+'</p>':'';pcount.textContent='';return}
      indexes().then(function(idx){
        if(my!==pseq)return;
        var res=searchAll(q,idx);
        if(res.pages.length){pbox.innerHTML=pagesHtml(res,q,0,false);pcount.textContent=count(res);return}
        pcount.textContent='';
        (alsoOn()?Promise.resolve(null):load(cfg.other).catch(function(){return null})).then(function(X2){
          if(my===pseq)pbox.innerHTML=emptyHtml(q,idx[0],X2,false);
        });
      }).catch(function(){if(my===pseq)pbox.innerHTML=emptyHtml(q,null,null,false)});
    };
    var q0='';try{q0=new URLSearchParams(location.search).get('q')||''}catch(e){}
    pin.value=q0;
    pin.addEventListener('focus',function(){load(cfg.lang)});
    var ptimer;pin.addEventListener('input',function(){clearTimeout(ptimer);ptimer=setTimeout(runPage,120)});
    page.querySelector('.sp-form').addEventListener('submit',function(e){e.preventDefault();runPage()});
    wireAlso(page.querySelector('.sp-also'),function(){runPage();if(isOpen())runPanel()});
    wireResults(pbox,function(s){pin.value=s;runPage()});
    if(q0)runPage();else pin.focus();
  }

  // ---------- arriving on a passage: reveal, scroll, highlight ----------
  var marks=[],lit=null,fadeT=0,clearT=0;
  function domHit(w,ts,ex){
    var ws=words(w);
    for(var n=0;n<ws.length;n++){var vs=variants(ws[n]);for(var k=0;k<vs.length;k++)for(var j=0;j<ts.length;j++){
      var t=ts[j];if(vs[k]===t||(!(ex&&ex.has(t))&&quality(t,vs[k])>=.5))return true}}
    return false;
  }
  function matches(el,ts,ex){                                 // does the element hold every term?
    var set=el.textContent.match(OWORD)||[];
    return ts.every(function(t){return set.some(function(w){return domHit(w,[t],ex)})});
  }
  function firstMatch(ts,ex){
    var els=document.querySelectorAll('main [data-p]');
    for(var n=0;n<els.length;n++)if(matches(els[n],ts,ex))return els[n];
    return null;
  }
  function unmark(){
    clearTimeout(fadeT);clearTimeout(clearT);
    marks.forEach(function(m){var p=m.parentNode;if(!p)return;p.replaceChild(document.createTextNode(m.textContent),m);p.normalize()});
    marks=[];
    if(lit){lit.classList.remove('hl-on','hl-fade');lit=null}
  }
  function mark(el,ts,ex){
    var walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
      var p=n.parentNode;return p.closest('svg,script,style,.g-anchor,.hxb,[aria-hidden="true"]')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
    var nodes=[],n;while((n=walker.nextNode()))nodes.push(n);
    nodes.forEach(function(node){
      var t=node.nodeValue,ranges=[];
      t.replace(OWORD,function(w,i){if(domHit(w,ts,ex))ranges.push([i,i+w.length])});
      if(!ranges.length)return;
      var frag=document.createDocumentFragment(),last=0;
      ranges.forEach(function(r){
        if(r[0]>last)frag.appendChild(document.createTextNode(t.slice(last,r[0])));
        var m=document.createElement('mark');m.className='hl-mark';m.textContent=t.slice(r[0],r[1]);frag.appendChild(m);marks.push(m);last=r[1];
      });
      if(last<t.length)frag.appendChild(document.createTextNode(t.slice(last)));
      node.parentNode.replaceChild(frag,node);
    });
  }
  function reveal(el){
    for(var p=el;p&&p!==document.body;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true}
    el.querySelectorAll('.faq-item>button[aria-expanded="false"]').forEach(function(b){b.click()});
    var sheet=document.querySelector('.g-toc.open .g-toc-close');if(sheet)sheet.click();
  }
  function place(el){el.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'})}
  // go to a passage of this page and light up the query's words in it (also used by the in-article finder)
  function go(q,id,opt){
    opt=opt||{};
    var ts=terms(q||''),ex=caps(q||''),el=id?document.getElementById(id):null;
    (opt.extra||[]).forEach(function(t){ex.add(t)});
    if(!el&&ts.length)el=firstMatch(ts,ex);
    unmark();
    if(!el){if(!opt.quiet)window.scrollTo(0,0);return null}
    reveal(el);place(el);
    if(!el.hasAttribute('tabindex'))el.setAttribute('tabindex','-1');
    el.focus({preventScroll:true});
    if(ts.length)mark(el,ts.concat(opt.extra||[]),ex);
    lit=el;el.classList.add('hl-on');
    var hold=opt.hold?6000:3000;
    fadeT=setTimeout(function(){
      if(reduce){unmark();return}
      el.classList.add('hl-fade');marks.forEach(function(m){m.classList.add('hl-fade')});
      clearT=setTimeout(unmark,900);
    },hold);
    return el;
  }
  function arrive(){
    var q=null;try{q=new URLSearchParams(location.search).get('hl')}catch(e){}
    if(q===null)return;
    var id='';try{id=decodeURIComponent(location.hash.slice(1))}catch(e){}
    try{var u=new URL(location.href);u.searchParams.delete('hl');history.replaceState(history.state,'',u.pathname+u.search+u.hash)}catch(e){}
    var el=go(q,id);
    if(el&&document.readyState!=='complete'){
      var y=window.scrollY;
      window.addEventListener('load',function(){if(Math.abs(window.scrollY-y)<200)el.scrollIntoView({block:'start'})},{once:true});
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',arrive);else arrive();

  // for the in-article finder (guide.js)
  window.ASASearch={load:function(){return load(cfg.lang)},run:run,go:go,terms:terms,snippet:snippet,esc:esc,hl:hl,
    words:words,variants:variants,clear:unmark,lang:cfg.lang};
})();
