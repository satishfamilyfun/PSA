import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("shows the message", () => {
    render(<EmptyState message="No photos yet" />);
    expect(screen.getByRole("status").textContent).toBe("No photos yet");
  });
});
