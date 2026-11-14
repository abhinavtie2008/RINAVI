import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteNav } from "./SiteNav";

describe("SiteNav", () => {
  it("links to the applications and locker pages", () => {
    render(<SiteNav />);

    expect(
      screen.getByRole("link", { name: "Applications" }),
    ).toHaveAttribute("href", "/applications");
    expect(screen.getByRole("link", { name: "Locker" })).toHaveAttribute(
      "href",
      "/locker",
    );
  });
});
