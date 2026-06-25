import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import { CommentThread } from "../CommentThread";
import type { Comment } from "../../types";

describe("CommentThread", () => {
  it("shows empty message when no comments", () => {
    render(<CommentThread comments={[]} />);
    expect(screen.getByText("No comments")).toBeInTheDocument();
  });

  it("renders comments in chronological order", () => {
    const comments: Comment[] = [
      {
        schema_version: 1,
        created_at: "2026-01-03T00:00:00Z",
        body: "Third",
      },
      {
        schema_version: 1,
        created_at: "2026-01-01T00:00:00Z",
        body: "First",
      },
      {
        schema_version: 1,
        created_at: "2026-01-02T00:00:00Z",
        body: "Second",
      },
    ];
    render(<CommentThread comments={comments} />);

    const bodies = screen.getAllByText(/^(First|Second|Third)$/);
    const bodyTexts = bodies.map((el) => el.textContent);
    expect(bodyTexts).toEqual(["First", "Second", "Third"]);
  });

  it("shows author name when created_by is provided", () => {
    const comments: Comment[] = [
      {
        schema_version: 1,
        created_at: "2026-01-01T00:00:00Z",
        body: "Test comment",
        created_by: "Alice",
      },
    ];
    render(<CommentThread comments={comments} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });

  it("shows Anonymous when created_by is missing", () => {
    const comments: Comment[] = [
      {
        schema_version: 1,
        created_at: "2026-01-01T00:00:00Z",
        body: "Test comment",
      },
    ];
    render(<CommentThread comments={comments} />);
    expect(screen.getByText("Anonymous")).toBeInTheDocument();
  });
});
