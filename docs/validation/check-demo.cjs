/* Usage: NODE_PATH=/path/to/node_modules node docs/validation/check-demo.cjs */
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

const demo = path.resolve(__dirname, "../demo/heatguard_demo.html");

async function main() {
  const browser = await chromium.launch({ channel: "chrome" });
  try {
    const context = await browser.newContext({ offline: true, viewport: { width: 1440, height: 1050 } });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(pathToFileURL(demo).href);
    assert.equal(await page.locator("#board .tile").count(), 12);
    assert.equal(await page.locator("#picker .pick").count(), 5);
    console.log("D01 PASS: offline page shows 12 workers and five individual shift stories");

    const firstStory = page.locator("#picker .pick").first();
    await firstStory.focus();
    await firstStory.press("Enter");
    assert.equal(await firstStory.getAttribute("aria-pressed"), "true");
    assert.match(await page.locator("#who-id").innerText(), /\d{4}-\d{2}-\d{2}/);
    console.log("D02 PASS: keyboard selection updates the worker detail");

    await page.locator("#reset").click();
    assert.equal(await page.locator("#time").innerText(), "06:00");
    assert.equal(await page.locator("#w-state").innerText(), "OK");
    await page.locator("#j-warn").click();
    assert.equal(await page.locator("#w-state").innerText(), "STOP");
    assert.match(await page.locator("#w-sub").innerText(), /rest in shade/);
    console.log("D03 PASS: reset returns OK at 06:00 and the first warning shows STOP");

    const slider = page.locator("#scrub");
    async function scrub(minute) {
      await slider.evaluate((control, value) => {
        control.value = String(value);
        control.dispatchEvent(new Event("input", { bubbles: true }));
      }, minute);
    }
    async function inject(button, minute) {
      await scrub(minute);
      await page.locator(button).click();
      await page.locator("#play").click(); // Pause the replay started by the fault control.
    }

    await inject("#f-drop", 60);
    await scrub(65);
    assert.equal(await page.locator("#fallback").isVisible(), true);
    assert.match(await page.locator("#fallback").innerText(), /No heart-rate reading.*WBGT rule/);
    assert.match(await page.locator("#v-hr").innerText(), /no reading/i);
    console.log("D04 PASS: dropout hides the heart-rate value and shows WBGT fallback");

    await page.locator("#f-clear").click();
    await inject("#f-stuck", 60);
    await scrub(66);
    assert.equal(await page.locator("#fallback").isVisible(), true);
    assert.match(await page.locator("#fallback").innerText(), /frozen.*WBGT rule/);
    console.log("D05 PASS: a detected frozen reading is labelled and switches to WBGT");

    await page.locator("#f-clear").click();
    assert.equal(await page.locator("#fallback").isVisible(), false);
    assert.match(await page.locator("#v-hr").innerText(), /\d+\s*bpm/);
    console.log("D06 PASS: Repair sensor clears fallback and restores a heart-rate value");

    await page.locator("#board .tile").first().click();
    assert.equal(await page.locator("#board .tile").first().getAttribute("aria-pressed"), "true");
    await scrub(400);
    assert.equal(await page.locator("#w-state").innerText(), "BREAK");
    assert.equal(await page.locator("#phase").innerText(), "LEGAL BREAK");
    console.log("D07 PASS: supervisor tile selects its worker and displays the legal break");

    await page.setViewportSize({ width: 390, height: 844 });
    const clockFits = await page.locator("#scrub").evaluate((control) => {
      const bounds = control.getBoundingClientRect();
      return bounds.left >= 0 && bounds.right <= window.innerWidth;
    });
    assert.equal(clockFits, true);
    assert.equal(await page.locator("#w-state").innerText(), "BREAK");
    assert.deepEqual(errors, []);
    console.log("D08 PASS: clock and worker status load at 390 px without a page error");
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
