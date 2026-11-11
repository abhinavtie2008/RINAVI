import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppBanner } from "./AppBanner";

describe("AppBanner", () => {
  it("renders the product name", () => {
    render(<AppBanner />);
    expect(screen.getByTestId("app-banner")).toHaveTextContent("RINAVI");
  });
});
