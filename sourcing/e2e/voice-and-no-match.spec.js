"use strict";
const {test,expect}=require("@playwright/test");
test("user-triggered speech parses a product and initiates a search without requiring delivery",async({page})=>{
 await page.addInitScript(()=>{
  window.SpeechRecognition=class{
   start(){
    queueMicrotask(()=>{
     this.onresult?.({results:[[{transcript:"найди ABB DI524 2 шт"}]]});
     this.onend?.();
    });
   }
   stop(){this.onend?.();}
  };
 });
 await page.goto("/sourcing.html?lang=ru");
 await expect(page.locator("#voiceSearch")).toBeVisible();
 await page.locator("#voiceSearch").click();
 await expect(page.locator("#part")).toHaveValue("ABB DI524");
 await expect(page.locator("#qty")).toHaveValue("2");
 await expect(page.locator("#results .gt-price-empty")).toBeVisible();
 await expect(page.locator("#results .gt-price-catalog")).toBeAttached();
 await expect(page.locator("#count")).toContainText("0");
});
test("typed search without destination works but RFQ still requires destination",async({page})=>{
 await page.goto("/sourcing.html?lang=en");
 await page.locator("#part").fill("rare discontinued item XU-9000123");
 await page.locator("#dest").fill("");
 await page.locator("#search").click();
 await expect(page.locator("#results .gt-price-empty")).toBeVisible();
 await expect(page.locator("#results .gt-source-card")).toHaveCount(12);
 await page.locator("#add").click();
 await expect(page.locator("#count")).toContainText("0");
});
