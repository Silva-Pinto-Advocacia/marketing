// Estilo misto, passo 3: quadros do reel (Chromium) e a conferência "nada sobre o rosto".
//   node render.js <projeto> teste 0.5 3.2 ...     prévias em <projeto>/teste/ (e as colisões no terminal)
//   node render.js <projeto> conferir              passa o vídeo inteiro a cada 0,1 s sem gravar nada
//   node render.js <projeto> tudo [workers]        confere e grava <projeto>/out/o00001.jpg ... (retoma de onde parou)
// Se algum texto, etiqueta, logo ou brasão encostar no rosto, ou a legenda encostar no texto da cena, `conferir` e `tudo` param com código 4 e
// listam onde (gravado também em <projeto>/colisoes.json). `tudo --forcar` renderiza mesmo assim.
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const SK=path.resolve(__dirname,'../..'), ICD=SK+'/assets/icons';
(async()=>{
  const [proj,modo,...resto]=process.argv.slice(2); const P=path.resolve(proj);
  const S=JSON.parse(fs.readFileSync(P+'/cenas.json')), RO=JSON.parse(fs.readFileSync(P+'/rosto.json'));
  const icons={}; for(const f of fs.readdirSync(ICD)) icons[f.replace('.svg','')]=fs.readFileSync(ICD+'/'+f,'utf8').replace(/\s(width|height)="24"/g,'');
  fs.writeFileSync(P+'/comp.built.html',fs.readFileSync(__dirname+'/comp_misto.html','utf8').split('__ASSETS__').join('file://'+SK+'/assets'));
  const b=await chromium.launch({args:['--allow-file-access-from-files']});
  async function pagina(){const p=await b.newPage({viewport:{width:1080,height:1920}});await p.goto('file://'+P+'/comp.built.html');
    await p.evaluate(([s,r,i])=>init(s,r,i),[S,RO,icons]);await p.evaluate(()=>document.fonts.ready);return p}
  const relatar=(cols)=>{ if(!cols.length){fs.rmSync(P+'/colisoes.json',{force:true});console.log('rosto livre: nenhum texto sobre o rosto nem legenda sobre outro texto');return 0}
    const por={}; for(const c of cols){const k=c.el+' | '+c.txt; (por[k]=por[k]||[]).push(c.t)}
    fs.writeFileSync(P+'/colisoes.json',JSON.stringify(cols));
    console.log('COLISÕES (texto sobre o rosto ou legenda sobre outro texto):'); for(const [k,ts] of Object.entries(por)) console.log(`  ${ts[0].toFixed(2)}-${ts[ts.length-1].toFixed(2)}s  ${k}`);
    return 4 };
  const N=Math.round(S.total*30); let codigo=0;
  if(modo==='teste'){ fs.mkdirSync(P+'/teste',{recursive:true}); const p=await pagina();
    for(const t of resto.map(Number)){await p.evaluate(t=>render(t),t);await p.screenshot({path:`${P}/teste/t${t.toFixed(2).padStart(6,'0')}.jpg`,type:'jpeg',quality:85})}
    relatar(await p.evaluate(()=>window.__colisoes));
  } else {
    const p=await pagina(); for(let f=0;f<N;f+=3) await p.evaluate(t=>render(t),f/30);
    codigo=relatar(await p.evaluate(()=>window.__colisoes)); await p.close();
    if(modo==='tudo'&&(codigo===0||resto.includes('--forcar'))){
      const out=P+'/out', wk=+(resto.find(x=>/^\d+$/.test(x))||4); fs.mkdirSync(out,{recursive:true});
      const todo=[...Array(N).keys()].filter(f=>!fs.existsSync(`${out}/o${String(f+1).padStart(5,'0')}.jpg`));
      await Promise.all([...Array(wk).keys()].map(async k=>{const p=await pagina();
        for(const f of todo.filter((_,i)=>i%wk===k)){await p.evaluate(t=>render(t),f/30);await p.screenshot({path:`${out}/o${String(f+1).padStart(5,'0')}.jpg`,type:'jpeg',quality:92})}}));
      console.log(`${N} quadros em ${out}`);
    }
  }
  await b.close(); process.exit(codigo);
})();
