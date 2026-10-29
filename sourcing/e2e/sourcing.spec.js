"use strict";
const {test,expect}=require("@playwright/test");

test("three languages, global search, source status and pagination",async({page})=>{
  await page.goto("/sourcing.html?lang=ru");
  await expect(page.locator("#part")).toBeVisible();
  await page.locator("#part").fill("Siemens 6ES7315-2EH14-0AB0");
  await page.locator("#qty").fill("2");
  await page.locator("#dest").fill("Istanbul, Türkiye");
  await page.locator("#search").click();
  await expect(page.locator("#results.gt-source-results")).toBeVisible();
  await expect(page.locator("#results .gt-source-card")).toHaveCount(12);
  await page.locator("#results .gt-source-more").click();
  await expect(page.locator("#results .gt-source-card")).toHaveCount(24);
  await expect(page.locator("#results")).toContainText(/310/);
  for(const locale of ["en","tr","ru"]){
    await page.locator("#lang").selectOption(locale);
    await expect(page.locator("#part")).toBeVisible();
  }
  await expect(page.locator("#add")).toBeVisible();
  await expect(page.locator("#wa")).toBeVisible();
  await expect(page.locator("#email")).toBeVisible();
  await expect(page.locator("#copy")).toBeVisible();
  await expect(page.locator("#extra")).toBeAttached();
  const links=await page.locator("#results .gt-source-card a").evaluateAll(els=>
    els.map(el=>({href:el.getAttribute("href"),target:el.getAttribute("target"),rel:el.getAttribute("rel")})));
  expect(links.length).toBeGreaterThanOrEqual(24);
  expect(links.every(x=>x.href?.startsWith("https://") && x.target==="_blank" && x.rel?.includes("noopener"))).toBeTruthy();
});
test("mobile viewport has no main horizontal overflow",async({page,isMobile})=>{
  await page.goto("/sourcing.html?lang=en");
  await expect(page.locator("#search")).toBeVisible();
  if(isMobile){
    const dimensions=await page.evaluate(()=>({viewport:document.documentElement.clientWidth,width:document.documentElement.scrollWidth}));
    expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport+2);
  }
});
