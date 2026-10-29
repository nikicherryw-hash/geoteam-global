"use strict";
const {test,expect}=require("@playwright/test");
test("price reference cards for Rotax 916",async({page})=>{
 await page.goto("/sourcing.html?lang=ru");
 await page.locator("#part").fill("ротокс 916");
 await page.locator("#qty").fill("1");
 await page.locator("#dest").fill("Istanbul, Türkiye");
 await page.locator("#search").click();
 await expect(page.locator(".gt-price-area")).toBeVisible();
 await expect(page.locator(".gt-price-item")).toHaveCount(5);
 await expect(page.locator(".gt-price-area")).toContainText("Lockwood Aero");
 await expect(page.locator(".gt-price-area")).toContainText("ROTOX");
 await page.locator(".gt-price-catalog summary").click();
 await expect(page.locator("#results .gt-source-card").first()).toBeVisible();
});
