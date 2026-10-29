/* GeoTeam Global v18.44: browser-initiated speech input. No recording stored by GeoTeam.
   Browser speech services may process audio remotely. Always user-initiated; typed fallback. */
(function(root,factory){
 "use strict";
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 root.GeoTeamVoiceInput=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 const TXT={
  ru:{start:"Диктовать запрос",stop:"Остановить диктовку",listening:"Слушаю… говорите название или артикул",unsupported:"Голосовой ввод этим браузером не поддерживается. Используйте микрофон клавиатуры.",denied:"Доступ к микрофону не предоставлен. Можно ввести запрос вручную.",error:"Не удалось распознать речь. Попробуйте снова или введите запрос.",privacy:"Распознавание выполняет браузер; он может отправлять аудио своему провайдеру.",done:"Распознано: "},
  en:{start:"Speak your request",stop:"Stop dictation",listening:"Listening… say the product or part number",unsupported:"Browser speech recognition is unavailable. Use keyboard dictation.",denied:"Microphone access is not allowed. Type your search instead.",error:"Could not recognize speech. Try again or type your query.",privacy:"Your browser recognizes speech and may process audio using an external provider.",done:"Recognized: "},
  tr:{start:"Talebinizi söyleyin",stop:"Sesli girişi durdur",listening:"Dinleniyor… ürün veya parça kodunu söyleyin",unsupported:"Tarayıcı konuşma tanıma desteklemiyor. Klavye diktesini kullanın.",denied:"Mikrofon izni verilmedi. Aramanızı yazabilirsiniz.",error:"Konuşma tanınamadı. Tekrar deneyin veya yazın.",privacy:"Konuşmayı tarayıcınız tanır; ses harici sağlayıcıya iletilebilir.",done:"Algılandı: "}
 };
 function clean(s){return String(s||"").normalize("NFKC").trim().replace(/\s+/g," ").slice(0,600);}
 function parse(raw){
  const text=clean(raw);if(!text)return {query:"",quantity:null,destination:"",condition:"any"};
  let q=text, destination="", quantity=null,condition="any";
  const mDest=q.match(/\s+(?:доставка\s+(?:в|до)|доставить\s+(?:в|до)|delivery\s+to|ship\s+to|deliver\s+to|teslimat\s+(?:yeri|için)|gönderim\s+(?:yeri|için))\s+(.+)$/iu);
  if(mDest){destination=mDest[1].trim().slice(0,100);q=q.slice(0,mDest.index).trim();}
  const mQty=q.match(/(?:^|\s)(\d{1,6})\s*(?:штук|штуки|шт\.?|pieces|pcs|units|adet)(?=\s|$)/iu)||q.match(/(?:^|\s)(?:количество|quantity|qty|miktar)\s*[:=]?\s*(\d{1,6})(?=\s|$)/iu);
  if(mQty){quantity=Number(mQty[1]);q=q.replace(mQty[0]," ").trim();}
  const cond=q.match(/(?:^|\s)(?:состояние\s+)?(б\/у|подержанный|second.hand|used|ikinci\s+el)(?=\s|$)/iu);
  if(cond){condition="used";q=q.replace(cond[0]," ").trim();}
  const newMatch=q.match(/(?:^|\s)(?:состояние\s+)?(новый|новое|new|sıfır)(?=\s|$)/iu);
  if(newMatch){condition="new";q=q.replace(newMatch[0]," ").trim();}
  q=q.replace(/^(?:найди(?:те)?|поищи(?:те)?|покажи(?:те)?|найти|ищи|find|search(?:\s+for)?|look\s+for|bul|ara)\s+/iu,"").trim();
  return {query:q.slice(0,160),quantity,destination,condition,transcript:text};
 }
 function install(options){
  if(typeof document==="undefined")return false;
  const button=document.getElementById(options?.buttonId||"voiceSearch");
  const input=document.getElementById(options?.inputId||"part");
  const status=document.getElementById(options?.statusId||"voiceStatus");
  if(!button||!input||!status||button.dataset.voiceInstalled==="yes")return false;
  button.dataset.voiceInstalled="yes";
  const langField=document.getElementById("lang");
  const getLang=()=>["ru","tr","en"].includes(langField?.value)?langField.value:"en";
  const words=()=>TXT[getLang()];
  let instance=null;
  const notify=(message)=>{status.textContent=message;};
  const Recognition=typeof window!=="undefined"?(window.SpeechRecognition||window.webkitSpeechRecognition):null;
  const update=()=>{button.setAttribute("aria-label",instance?words().stop:words().start);button.setAttribute("title",instance?words().stop:words().start);button.setAttribute("aria-pressed",instance?"true":"false");};
  button.addEventListener("click",()=>{
   if(instance){try{instance.stop();}catch{}instance=null;update();return;}
   if(!Recognition){notify(words().unsupported);input.focus();return;}
   try{
    const rec=new Recognition();instance=rec;rec.lang=getLang()==="ru"?"ru-RU":getLang()==="tr"?"tr-TR":"en-US";rec.maxAlternatives=1;rec.interimResults=false;rec.continuous=false;
    rec.onresult=(event)=>{
     const spoken=event?.results?.[0]?.[0]?.transcript||"";
     const result=parse(spoken);if(!result.query)return;
     input.value=result.query;input.dispatchEvent(new Event("input",{bubbles:true}));
     const qty=document.getElementById("qty");
     if(qty&&result.quantity&&result.quantity>=1&&result.quantity<=999999){qty.value=String(result.quantity);qty.dispatchEvent(new Event("input",{bubbles:true}));}
     const dest=document.getElementById("dest");if(dest&&result.destination){dest.value=result.destination;dest.dispatchEvent(new Event("input",{bubbles:true}));}
     const condition=document.getElementById("condition");if(condition&&result.condition!=="any")condition.value=result.condition;
     notify(words().done+spoken);
     const search=document.getElementById("search");if(search&&!search.disabled)search.click();
    };
    rec.onerror=(event)=>{notify(event?.error==="not-allowed"?words().denied:words().error);};
    rec.onend=()=>{instance=null;update();};
    notify(words().listening+" "+words().privacy);
    update();rec.start();
   }catch{instance=null;update();notify(words().error);}
  });
  langField?.addEventListener("change",update);update();
  return true;
 }
 return Object.freeze({parse,install});
});
