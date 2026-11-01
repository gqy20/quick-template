# Pages Redesign QA — 2026-08-31

## Comparison Target

- Source visual truth:
  `/home/qy113/.codex/generated_images/01a05692-29e4-71e3-a9c9-0a65d0f85836/exec-8a997c94-8390-4564-a3ac-e6b0f872137d.png`
- Browser-rendered implementation:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/08-desktop-refined.png`
- Full-view comparison:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/qa-full-comparison-refined.png`
- Focused hero comparison:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/qa-hero-comparison.png`
- State: light theme, default landing page, no browser chrome.
- Reference pixels: 906 × 1736.
- Implementation: 1440 × 3404 full-page capture at a 1440 × 900 CSS viewport,
  device scale factor 1.
- Normalization: the implementation was resized to 906px width for the full-view
  comparison. The focused hero comparison uses two 906 × 566 crops.

## Required Viewports

- 390 × 844:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/09-mobile-refined.png`
- 768 × 1024:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/10-tablet-refined.png`
- 1280 × 800:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/11-laptop-refined.png`
- 1440 × 900:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/08-desktop-refined.png`
- 1920 × 1080:
  `/home/qy113/workspace/tmp/quick-template-pages-implementation-20260831/12-wide-refined.png`

The page has no document-level horizontal overflow at 320px or 390px. The language
matrix and long commands use explicit local scroll containers. A 720px effective
CSS viewport was used as the 200% browser-zoom proxy because browser zoom changes
the CSS viewport rather than applying CSS `zoom`.

## Fidelity Review

- **Fonts and typography:** implementation follows the Geist / Noto Sans SC token
  stack and 16px readable body baseline. System fallbacks are used when those fonts
  are not installed. The H1 is intentionally smaller than the generated mock to
  respect the repository's 36–44px display contract.
- **Spacing and layout rhythm:** the asymmetric hero, right-side baseline map,
  alternating editorial bands, three-part Runtime relationship, language matrix,
  and final three-step action strip match the selected direction. Section padding
  was tightened in the second pass.
- **Colors and visual tokens:** canvas, surface, ink, border, accent, evidence, and
  state colors map directly to `shared/DESIGN.md`. There are no gradients, neon,
  glass surfaces, or decorative shadows.
- **Image and asset fidelity:** the page requires no raster imagery. The mock's
  unapproved icons and lightning glyph were omitted instead of recreating them with
  inline SVG, CSS drawings, or text symbols. The system relationship remains clear
  through ordered semantic content and borders.
- **Copy and content:** all visible claims were reconciled with the current README,
  templates, CI, and Agent Runtime implementation. Mock-only claims such as PyPI
  installation, fixed coverage thresholds, and security tooling were not copied.

## Comparison History

### Iteration 1 — blocked

- **P1:** copy control failed when browser clipboard permission was denied.
  Fixed by falling back to a local selection-and-copy path; browser interaction now
  reports `已复制`.
- **P2:** the first full-page implementation was materially taller and looser than
  the source direction. Fixed by reducing section padding, contract-row spacing,
  Runtime spacing, and final-action spacing while retaining 16px readable text.
- **P2:** the skip link changed the URL but did not move focus into the main region.
  Fixed by making the main landmark programmatically focusable.
- **P2:** the mobile language table scrolled locally but did not explain that
  behavior. Fixed with a narrow-screen scroll hint.

### Iteration 2 — passed

- Full-view and focused hero comparisons show the same hierarchy, section order,
  palette, primary action, evidence surface, and Runtime relationship.
- Copy, skip-link focus, anchor navigation, local table scrolling, reduced-motion
  media emulation, and responsive reflow were checked in the browser.
- Browser console contained no errors.
- No actionable P0, P1, or P2 findings remain.

## Follow-up Polish

- **P3:** self-host Geist and Noto Sans SC only if exact typography becomes more
  important than keeping the Pages artifact small and dependency-free.
- **P3:** add an approved brand-mark and icon library in a later brand pass; do not
  substitute handcrafted SVG or CSS illustrations.

## Verification

- Primary interactions: copy install command, skip to main content, anchor navigation.
- Accessibility structure: one H1, main landmark, labeled navigation, visible focus,
  44px copy target, safe external new-window link, responsive table hint.
- Static artifact validation: local assets, fragment targets, template-marker scan,
  current capability copy, and external-link safety.

final result: passed
