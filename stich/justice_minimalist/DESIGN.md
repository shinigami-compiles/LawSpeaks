# Design System Specification: The Judicial Monolith

## 1. Overview & Creative North Star
**Creative North Star: "The Digital Tabula Rasa"**

To design for the Indian legal sector is to design for clarity amidst complexity. This design system rejects the cluttered, bureaucratic aesthetic of traditional legal tech. Instead, it adopts a "High-End Editorial" approach. We treat the interface not as a software tool, but as a prestigious legal manuscript. 

The system moves beyond "standard" UI by leveraging **Organic Minimalism**. We break the rigid, boxy templates of typical AI assistants through intentional asymmetry, massive negative space, and a "Tonal Layering" philosophy. The result is an experience that feels authoritative yet approachable—a silent, powerful ally in legal self-defense.

---

## 2. Colors & Surface Philosophy
Our palette is a study in monochrome. By stripping away hue, we force the user to focus on the weight of the information.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections. Traditional boxes feel restrictive and "cheap." Instead, boundaries must be defined solely through:
- **Background Color Shifts:** A `surface-container-low` section sitting on a `surface` background.
- **Negative Space:** Using the spacing scale to create "invisible" containers.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—fine paper stacked on a stone plinth.
- **Base Layer:** `surface` (#f9f9fa) – The canvas.
- **Structural Nesting:** Use `surface-container-low` (#f3f3f4) for secondary sidebars and `surface-container-highest` (#e2e2e3) for active, high-priority interactive zones. 
- **The Glass & Gradient Rule:** For floating action buttons or sticky headers, use `surface-container-lowest` (#ffffff) with a 80% opacity and a `24px` backdrop-blur. This "frosted glass" effect prevents the UI from feeling flat and "pasted on."

### Signature Textures
To add "soul," use a subtle linear gradient on primary CTAs:
- **Primary Gradient:** `primary` (#000000) to `primary-container` (#3b3b3b) at a 135-degree angle. This creates a soft, metallic sheen reminiscent of high-end stationery.

---

## 3. Typography: The Editorial Voice
We use a dual-typeface system to balance the "Judicial" (Manrope) with the "Functional" (Inter).

*   **Display & Headlines (Manrope):** These are our "Statutory" weights. Use `display-lg` and `headline-md` with tight letter-spacing (-0.02em) to create a sense of monumental authority.
*   **Body & Titles (Inter):** Our "Testimony" weights. Inter provides exceptional readability for complex legal jargon. 
*   **Hierarchy as Authority:** Use `display-sm` for AI responses to give them the weight of a legal ruling, while user inputs stay in `title-md` to denote a conversational tone.

---

## 4. Elevation & Depth
Depth is achieved through **Tonal Layering**, not structural scaffolding.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` background. This creates a "soft lift" that feels natural and premium.
*   **Ambient Shadows:** If a card must float (e.g., a legal citation pop-up), use: `box-shadow: 0 12px 40px rgba(26, 28, 29, 0.06);`. The shadow color is a tint of `on-surface`, never pure black.
*   **The Ghost Border Fallback:** If a border is required for accessibility, use the `outline-variant` (#c6c6c6) at **15% opacity**. High-contrast borders are strictly forbidden.

---

## 5. Components

### Input Fields (The Inquiry)
- **Styling:** No bottom line or full box. Use `surface-container-low` with a `lg` (0.5rem) corner radius. 
- **States:** On focus, transition the background to `surface-container-lowest` and apply a subtle "Ghost Border."

### Buttons (The Verdict)
- **Primary:** Black (`primary`) with White (`on-primary`) text. High-contrast, sharp, and decisive.
- **Tertiary:** No background. Use `label-md` in `primary` with a subtle underline that appears only on hover.

### Legal "Evidence" Chips
- **Selection Chips:** Use `secondary-container` (#d5d4d4) with `on-secondary-container` (#1b1c1c) text. 
- **Shape:** Use the `full` (9999px) roundedness to contrast against the architectural `lg` radius of the main chat bubbles.

### Chat Interface (The Transcript)
- **User Bubbles:** Right-aligned, `surface-container-highest` background, no tail.
- **AI Bubbles:** Left-aligned, transparent background. Use the `headline-sm` for the initial summary line to provide immediate "Editorial" impact.
- **Anti-Divider Rule:** Forbid 1px dividers between messages. Use `40px` of vertical white space to separate user/AI turns.

---

## 6. Do's and Don'ts

### Do:
*   **Embrace the Void:** Use 1.5x more white space than you think you need. Space is a sign of luxury and calm.
*   **Layer with Intent:** Ensure every nested element is exactly one tier higher or lower than its parent surface.
*   **Use Subtle Micro-interactions:** Buttons should have a "weighted" feel—slight scale down (0.98) on click rather than a simple color change.

### Don't:
*   **No "Safety Blue":** Do not use blue for links or buttons. We use `primary` (black) or `secondary` (dark grey) to maintain the monochrome legal aesthetic.
*   **No Hard Shadows:** Never use `offset-y: 5px` with 20% opacity. It looks like 2010-era web design.
*   **No Grid Lines:** Do not use lines to separate the sidebar from the main chat. Use a background shift from `surface` to `surface-container-low`.