import { afterEach, describe, expect, it, vi } from "vitest";
import { unarchiveItem } from "./client";

describe("unarchiveItem", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the REST contract's POST method", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "TP-1" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await unarchiveItem("TP", "TP-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/projects/TP/items/TP-1/unarchive",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
