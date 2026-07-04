import { test, expect } from "@playwright/test";

test.describe("Design token themes (AC-3, AC-4, AC-5)", () => {
  test("AC-3: light defaults resolve via :root", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("/");

    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      const resolveColorToken = (
        tokenName: string,
        property: "backgroundColor" | "color",
      ) => {
        const element = document.createElement("div");
        element.style[property] = `var(${tokenName})`;
        document.body.append(element);
        const value = getComputedStyle(element)[property];
        element.remove();
        return value;
      };
      return {
        surfaceApp: resolveColorToken("--surface-app", "backgroundColor"),
        surfaceBase: resolveColorToken("--surface-base", "backgroundColor"),
        textPrimary: resolveColorToken("--text-primary", "color"),
        typeEpicBg: resolveColorToken("--type-epic-bg", "backgroundColor"),
        typeFeatureBg: resolveColorToken(
          "--type-feature-bg",
          "backgroundColor",
        ),
        typeFeatureFg: resolveColorToken("--type-feature-fg", "color"),
        typeTaskBg: resolveColorToken("--type-task-bg", "backgroundColor"),
        typeBugBg: resolveColorToken("--type-bug-bg", "backgroundColor"),
        typeBugFg: resolveColorToken("--type-bug-fg", "color"),
        viewportMinWidth: style.getPropertyValue("--viewport-min-width").trim(),
        contentMaxWidth: style.getPropertyValue("--content-max-width").trim(),
        kanbanColumnMin: style.getPropertyValue("--kanban-column-min").trim(),
        kanbanColumnMax: style.getPropertyValue("--kanban-column-max").trim(),
      };
    });

    expect(tokens.surfaceApp).toBe("rgb(248, 250, 252)");
    expect(tokens.surfaceBase).toBe("rgb(255, 255, 255)");
    expect(tokens.textPrimary).toBe("rgb(16, 42, 67)");
    expect(tokens.typeEpicBg).toBe("rgb(237, 233, 254)");
    expect(tokens.typeFeatureBg).toBe("rgb(30, 58, 138)");
    expect(tokens.typeFeatureFg).toBe("rgb(255, 255, 255)");
    expect(tokens.typeTaskBg).toBe("rgb(224, 242, 254)");
    expect(tokens.typeBugBg).toBe("rgb(248, 215, 218)");
    expect(tokens.typeBugFg).toBe("rgb(114, 28, 36)");
    expect(tokens.viewportMinWidth).toBe("1280px");
    expect(tokens.contentMaxWidth).toBe("1760px");
    expect(tokens.kanbanColumnMin).toBe("248px");
    expect(tokens.kanbanColumnMax).toBe("320px");
  });

  test("AC-4: data-theme=dark overrides apply dark tokens", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("/");
    await page.evaluate(() =>
      document.documentElement.setAttribute("data-theme", "dark"),
    );

    const tokens = await page.evaluate(() => {
      const resolveColorToken = (
        tokenName: string,
        property: "backgroundColor" | "color",
      ) => {
        const element = document.createElement("div");
        element.style[property] = `var(${tokenName})`;
        document.body.append(element);
        const value = getComputedStyle(element)[property];
        element.remove();
        return value;
      };
      return {
        surfaceApp: resolveColorToken("--surface-app", "backgroundColor"),
        surfaceBase: resolveColorToken("--surface-base", "backgroundColor"),
        textPrimary: resolveColorToken("--text-primary", "color"),
        typeEpicBg: resolveColorToken("--type-epic-bg", "backgroundColor"),
        typeFeatureBg: resolveColorToken(
          "--type-feature-bg",
          "backgroundColor",
        ),
        typeFeatureFg: resolveColorToken("--type-feature-fg", "color"),
        typeTaskBg: resolveColorToken("--type-task-bg", "backgroundColor"),
        typeBugBg: resolveColorToken("--type-bug-bg", "backgroundColor"),
        typeBugFg: resolveColorToken("--type-bug-fg", "color"),
      };
    });

    expect(tokens.surfaceApp).toBe("rgb(17, 17, 19)");
    expect(tokens.surfaceBase).toBe("rgb(28, 28, 30)");
    expect(tokens.textPrimary).toBe("rgb(245, 245, 247)");
    expect(tokens.typeEpicBg).toBe("rgb(59, 7, 100)");
    expect(tokens.typeFeatureBg).toBe("rgb(23, 37, 84)");
    expect(tokens.typeFeatureFg).toBe("rgb(191, 219, 254)");
    expect(tokens.typeTaskBg).toBe("rgb(8, 47, 73)");
    expect(tokens.typeBugBg).toBe("rgb(74, 26, 31)");
    expect(tokens.typeBugFg).toBe("rgb(242, 139, 149)");
  });

  test("AC-5: data-theme=light overrides when OS prefers dark", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");
    await page.evaluate(() =>
      document.documentElement.setAttribute("data-theme", "light"),
    );

    const tokens = await page.evaluate(() => {
      const resolveColorToken = (
        tokenName: string,
        property: "backgroundColor" | "color",
      ) => {
        const element = document.createElement("div");
        element.style[property] = `var(${tokenName})`;
        document.body.append(element);
        const value = getComputedStyle(element)[property];
        element.remove();
        return value;
      };
      return {
        surfaceApp: resolveColorToken("--surface-app", "backgroundColor"),
        surfaceBase: resolveColorToken("--surface-base", "backgroundColor"),
        textPrimary: resolveColorToken("--text-primary", "color"),
        // These two are #1a1a1a in dark; [data-theme="light"] flips
        // color-scheme so light-dark() returns the light value.
        accentFg: resolveColorToken("--accent-fg", "color"),
        statusInprogressFg: resolveColorToken(
          "--status-inprogress-fg",
          "color",
        ),
      };
    });

    expect(tokens.surfaceApp).toBe("rgb(248, 250, 252)");
    expect(tokens.surfaceBase).toBe("rgb(255, 255, 255)");
    expect(tokens.textPrimary).toBe("rgb(16, 42, 67)");
    expect(tokens.accentFg).toBe("rgb(255, 255, 255)");
    expect(tokens.statusInprogressFg).toBe("rgb(255, 255, 255)");
  });

  test("OS dark preference activates dark tokens automatically", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");

    const tokens = await page.evaluate(() => {
      const resolveColorToken = (
        tokenName: string,
        property: "backgroundColor" | "color",
      ) => {
        const element = document.createElement("div");
        element.style[property] = `var(${tokenName})`;
        document.body.append(element);
        const value = getComputedStyle(element)[property];
        element.remove();
        return value;
      };
      return {
        surfaceApp: resolveColorToken("--surface-app", "backgroundColor"),
        textPrimary: resolveColorToken("--text-primary", "color"),
      };
    });

    expect(tokens.surfaceApp).toBe("rgb(17, 17, 19)");
    expect(tokens.textPrimary).toBe("rgb(245, 245, 247)");
  });

  test("item type label token pairs meet normal-text contrast", async ({
    page,
  }) => {
    for (const colorScheme of ["light", "dark"] as const) {
      await page.emulateMedia({ colorScheme });
      await page.goto("/");

      const pairs = await page.evaluate(() => {
        const resolveColorToken = (
          tokenName: string,
          property: "backgroundColor" | "color",
        ) => {
          const element = document.createElement("div");
          element.style[property] = `var(${tokenName})`;
          document.body.append(element);
          const value = getComputedStyle(element)[property];
          element.remove();
          return value;
        };

        return ["epic", "feature", "task", "bug"].map((type) => ({
          type,
          background: resolveColorToken(
            `--type-${type}-bg`,
            "backgroundColor",
          ),
          foreground: resolveColorToken(`--type-${type}-fg`, "color"),
        }));
      });

      for (const pair of pairs) {
        expect(
          contrastRatio(pair.foreground, pair.background),
          `${colorScheme} ${pair.type} type contrast`,
        ).toBeGreaterThanOrEqual(4.5);
      }
    }
  });
});

function contrastRatio(foreground: string, background: string) {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

function relativeLuminance(rgb: string) {
  const [r, g, b] = rgb.match(/\d+/g)?.map(Number) ?? [];
  return [r, g, b]
    .map((channel) => {
      const normalized = channel / 255;
      return normalized <= 0.03928
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    })
    .reduce(
      (sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index],
      0,
    );
}
