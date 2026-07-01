const { test, expect } = require("@playwright/test");

const answers = [
  ["cahaya", "rendah"],
  ["penyiraman", "jarang"],
  ["posisi", "indoor"],
  ["ruang", "kecil"],
  ["perawatan", "mudah"],
  ["hewan_peliharaan", "tidak"],
  ["nyaman_duri", "tidak"],
  ["budget", "rendah"],
  ["jenis_tampilan", "daun"],
  ["ukuran", "kecil"],
];

async function expectNoHorizontalOverflow(page) {
  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(hasOverflow).toBe(false);
}

async function expectImageAssetsReachable(page) {
  const sources = await page.evaluate(() => Array.from(document.images).map((image) => image.currentSrc || image.src));
  const failures = [];

  for (const source of sources) {
    const response = await page.request.get(source);
    if (!response.ok()) failures.push({ source, status: response.status() });
  }

  expect(failures).toEqual([]);
}

async function completeRecommendationForm(page) {
  await page.goto("/rekomendasi");

  for (const [name, value] of answers) {
    const choice = page.locator(`.question-step:not([hidden]) label.choice-chip:has(input[name="${name}"][value="${value}"])`);
    await expect(choice).toHaveCount(1);
    await choice.click();
  }
}

async function expectResultTextAlignedWithCards(page) {
  const boxes = await page.evaluate(() => {
    const hero = document.querySelector(".recommendation-hero--result > div").getBoundingClientRect();
    const summary = document.querySelector(".result-summary").getBoundingClientRect();
    const card = document.querySelector(".result-card").getBoundingClientRect();

    return {
      heroLeft: hero.left,
      summaryLeft: summary.left,
      cardLeft: card.left,
    };
  });

  expect(Math.abs(boxes.heroLeft - boxes.cardLeft)).toBeLessThanOrEqual(2);
  expect(Math.abs(boxes.summaryLeft - boxes.cardLeft)).toBeLessThanOrEqual(2);
}

test("main pages render without overflow or broken images", async ({ page }) => {
  for (const path of ["/", "/rekomendasi", "/tentang"]) {
    await page.goto(path);

    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", "id");
    const headerTop = await page.evaluate(() => Math.round(document.querySelector(".site-header").getBoundingClientRect().top));
    expect(headerTop).toBe(0);
    await expectNoHorizontalOverflow(page);
    await expectImageAssetsReachable(page);
  }
});

test("about references are clickable links without visible raw URLs", async ({ page }) => {
  await page.goto("/tentang");

  const referenceTitles = [
    "Implementasi Forward Chaining Pada Sistem Pakar Deteksi Kesuburan Tanah Sebagai Media Tanah di Lahan Pertanian",
    "Sistem Pakar Pemilihan Bibit Padi Unggul dengan Metode Forward Chaining",
    "Growing Indoor Plants with Success",
  ];
  const visibleText = await page.locator("main").innerText();

  for (const title of referenceTitles) {
    const link = page.getByRole("link", { name: new RegExp(title) });
    await expect(link).toHaveCount(1);
    const href = await link.getAttribute("href");
    expect(href).toMatch(/^https:\/\//);
    await expect(link).toHaveAttribute("target", "_blank");
    await expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(visibleText).not.toContain(href);
  }
});

test("recommendation form completes and resets", async ({ page }) => {
  await page.goto("/rekomendasi");

  await expect(page.getByText("cari tanaman yang pas.")).toBeVisible();
  await expect(page.getByText("Isi pilihan seperti memilih moodboard mini. Setiap jawaban membantu FLORA mencocokkan kondisi ruang dengan data tanaman hias.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Jawab satu per satu" })).toBeVisible();
  await expect(page.locator(".question-step:not([hidden])")).toHaveCount(1);
  await expect(page.locator(".progress-copy")).toHaveText("1 / 10");
  await expect(page.locator(".question-step:not([hidden]) legend")).not.toContainText("Pertanyaan 1 dari 10");

  await page.locator('.question-step:not([hidden]) label.choice-chip:has(input[name="cahaya"][value="rendah"])').click();
  await expect(page.locator(".progress-copy")).toHaveText("2 / 10");
  await expect(page.locator('.question-step:not([hidden]) input[name="penyiraman"]')).toHaveCount(3);

  for (const [name, value] of answers.slice(1)) {
    const choice = page.locator(`.question-step:not([hidden]) label.choice-chip:has(input[name="${name}"][value="${value}"])`);
    await expect(choice).toHaveCount(1);
    await choice.click();
  }

  await expect(page.getByText("Hasil rekomendasi", { exact: true })).toBeVisible();
  await expect(page.getByText("pilihan tanamanmu sudah siap.")).toBeVisible();
  await expect(page.getByText("FLORA menampilkan tanaman yang paling sesuai berdasarkan jawabanmu, lengkap dengan ringkasan perawatan dan alasan kecocokannya.")).toBeVisible();
  await expect(page.getByText("Isi pilihan seperti memilih moodboard mini. Setiap jawaban membantu FLORA mencocokkan kondisi ruang dengan data tanaman hias.")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /Sansevieria menjadi pilihan utama/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sansevieria", exact: true })).toBeVisible();
  await expect(page.getByRole("img", { name: "Foto tanaman Sansevieria" })).toBeVisible();
  await expect(page.getByText("Atribut tanaman")).toHaveCount(0);
  await expect(page.getByText("Mengapa cocok?")).toBeVisible();
  await expect(page.getByText("Catatan singkat")).toBeVisible();
  expect(await page.locator(".match-list li").count()).toBeLessThanOrEqual(4);

  await page.getByRole("link", { name: "Rekomendasi Lagi" }).click();
  await expect(page.getByRole("heading", { name: "Jawab satu per satu" })).toBeVisible();
});

for (const width of [950, 1024, 1366]) {
  test(`recommendation result text aligns with result cards at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await completeRecommendationForm(page);

    await expect(page.locator(".recommendation-hero--result")).toBeVisible();
    await expectResultTextAlignedWithCards(page);
    await expectNoHorizontalOverflow(page);
  });
}

test("previous button preserves selected answers", async ({ page }) => {
  await page.goto("/rekomendasi");

  await page.locator('.question-step:not([hidden]) label.choice-chip:has(input[name="cahaya"][value="rendah"])').click();
  await expect(page.locator('.question-step:not([hidden]) input[name="penyiraman"]')).toHaveCount(3);

  await page.getByRole("button", { name: "Sebelumnya" }).click();

  const repeatedChoice = page.locator('.question-step:not([hidden]) label.choice-chip:has(input[name="cahaya"][value="rendah"])');
  await expect(page.locator('.question-step:not([hidden]) input[name="cahaya"][value="rendah"]')).not.toBeChecked();
  await repeatedChoice.click();
  await expect(page.locator('.question-step:not([hidden]) input[name="penyiraman"]')).toHaveCount(3);
});

test("mobile burger menu opens and navigates", async ({ page, isMobile }) => {
  test.skip(!isMobile, "Mobile navigation is only visible on mobile projects.");

  await page.goto("/");
  const burger = page.locator("[data-burger]");

  await expect(burger).toBeVisible();
  await burger.click();
  await expect(burger).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByRole("navigation", { name: "Navigasi mobile" })).toBeVisible();

  await page.getByRole("navigation", { name: "Navigasi mobile" }).getByRole("link", { name: "Tentang" }).click();
  await expect(page).toHaveURL(/\/tentang$/);
  await expect(page.getByRole("heading", { name: "Anggota Kelompok" })).toBeVisible();
});

test("mobile recommendation progress stays in the top-right", async ({ page, isMobile }) => {
  test.skip(!isMobile, "Mobile layout check is only visible on mobile projects.");

  await page.goto("/rekomendasi");
  await expect(page.locator(".progress-copy")).toHaveText("1 / 10");

  const boxes = await page.evaluate(() => {
    const header = document.querySelector(".stage-header").getBoundingClientRect();
    const progress = document.querySelector(".progress-copy").getBoundingClientRect();
    return {
      headerTop: header.top,
      headerRight: header.right,
      progressTop: progress.top,
      progressRight: progress.right,
      progressLeft: progress.left,
    };
  });

  expect(Math.abs(boxes.progressTop - boxes.headerTop)).toBeLessThanOrEqual(8);
  expect(Math.abs(boxes.headerRight - boxes.progressRight)).toBeLessThanOrEqual(2);
  expect(boxes.progressLeft).toBeGreaterThan(0);
});

test("keyboard can use skip link and recommendation options", async ({ page }) => {
  await page.goto("/");

  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Lewati ke konten utama" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  await page.goto("/rekomendasi");
  await page.locator('.question-step:not([hidden]) input[name="cahaya"][value="rendah"]').focus();
  await page.keyboard.press("Space");

  await expect(page.locator(".progress-copy")).toHaveText("2 / 10");
  await expect(page.locator('.question-step:not([hidden]) input[name="penyiraman"]')).toHaveCount(3);
});
