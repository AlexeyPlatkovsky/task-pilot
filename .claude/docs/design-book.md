# TaskPilot Design Book

Status: baseline

## Product Experience

TaskPilot is a local developer tool for inspecting and changing structured work shared with AI
agents. The interface prioritizes fast scanning, explicit system state, keyboard use, and
Git-friendly transparency over dashboard decoration.

## Core Patterns

- Use a list or table as the primary scanning surface.
- Use a detail page or side panel for one item's content, metadata, links, and comments.
- Show validation close to the affected field and preserve visibility of invalid source files.
- Show statuses and relationship types with text; color may reinforce meaning but cannot own it.
- Keep destructive actions explicit and confirm effects that can remove canonical data.
- Keep domain rules and filesystem behavior outside UI components.

## Required States

Every applicable product flow accounts for:

- loading;
- empty results;
- recoverable error;
- invalid canonical file;
- missing or broken relation;
- unsaved or conflicting change;
- completed success state;
- narrow-screen layout.

## Accessibility Baseline

- All controls have accessible names.
- Keyboard order follows the visible task flow.
- Focus remains visible and moves deliberately after dialogs, drawers, and create actions.
- Native controls and accessible primitives are preferred.
- Status, priority, validation, and relationship meaning never depend on color alone.

## Responsive Baseline

- Desktop layouts optimize for scanning and side-by-side context.
- Narrow layouts preserve the primary action and item identity before secondary metadata.
- Tables may become stacked rows only when column meaning remains explicit.

## Visual Direction

- Neutral surfaces, restrained borders, one functional accent, and clear type hierarchy.
- Consistent spacing and density suitable for developer tools.
- Motion is limited to opacity and transforms that clarify state changes.
- Avoid glass effects, decorative gradients, dashboard-card overload, and hidden hover-only state.

## Design Debt

- No production UI exists yet, so component tokens, exact density, breakpoints, and interaction
  behavior remain provisional.
- Update this book when an accepted specification or implemented UI establishes a durable pattern.
