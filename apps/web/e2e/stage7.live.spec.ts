import { expect, test } from "@playwright/test";
import path from "node:path";

test.skip(process.env.SHOPLENS_E2E_LIVE !== "1", "Set SHOPLENS_E2E_LIVE=1 against the running Compose stack.");

test("live HTTP demo flow: agent, evidence, image, comparison, and trace", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("搜索词").fill("1000 元以内，头戴式，地铁通勤，降噪强，戴眼镜尽量舒服。");
  await page.getByRole("button", { name: "开始导购" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.locator(".result-grid > li").first()).toBeVisible();
  await expect(page.getByText("当前有效条件")).toBeVisible();
  await page.getByRole("link", { name: "查看事实与全部证据 →" }).first().click();
  await expect(page.getByRole("heading", { name: "商品事实", exact: true })).toBeVisible();

  await page.goto("/");
  await page.getByRole("radio", { name: "图片 + 文字" }).check();
  await page.getByLabel("搜索词").fill("找外观相近的黑色款，预算降到 800");
  await page.getByLabel("最高价格").fill("800");
  await page.getByLabel("参考图片").setInputFiles(path.resolve(process.cwd(), "../../data/fixtures/images/fixture-001.png"));
  await page.getByRole("button", { name: "开始检索" }).click();
  await expect(page).toHaveURL(/\/results$/);
  const cards = page.locator(".result-grid > li");
  await expect(cards.first()).toBeVisible();
  await cards.nth(0).getByRole("button", { name: "加入对比", exact: true }).click();
  await cards.nth(1).getByRole("button", { name: "加入对比", exact: true }).click();
  await page.getByRole("link", { name: /对比 2 件商品/ }).click();
  await expect(page.getByRole("table")).toBeVisible();
});
