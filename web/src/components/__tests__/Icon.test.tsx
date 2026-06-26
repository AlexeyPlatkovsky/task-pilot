import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Icon } from "../ui/Icon";

// Minimal SVG mock — tests Icon's accessibility contract without importing lucide-react
function TestIcon({
  size,
  ...rest
}: { size?: number } & React.SVGProps<SVGSVGElement>) {
  return <svg width={size} height={size} {...rest} />;
}

describe("Icon — accessibility contract (AC-6, AC-7, AC-8)", () => {
  it("renders svg with aria-label and aria-hidden=false when label is provided", () => {
    const { container } = render(<Icon icon={TestIcon} label="epic" />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg).toHaveAttribute("aria-label", "epic");
    expect(svg).toHaveAttribute("aria-hidden", "false");
  });

  it("does not have aria-label attribute when label is absent", () => {
    const { container } = render(<Icon icon={TestIcon} />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg).not.toHaveAttribute("aria-label");
  });

  it("renders svg with aria-hidden=true when label is absent", () => {
    const { container } = render(<Icon icon={TestIcon} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
  });

  it("applies the default size of 16 to width and height", () => {
    const { container } = render(<Icon icon={TestIcon} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "16");
    expect(svg).toHaveAttribute("height", "16");
  });

  it("applies a custom size when provided", () => {
    const { container } = render(<Icon icon={TestIcon} size={24} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
  });
});
