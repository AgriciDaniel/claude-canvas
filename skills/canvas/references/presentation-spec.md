# Presentation Mode Specification

Build slide-deck canvases that work with the [Advanced Canvas](https://github.com/Developer-Mike/obsidian-advanced-canvas) plugin's presentation mode.

---

## How Presentation Mode Works

Advanced Canvas adds arrow-key navigation to Obsidian Canvas. Each "slide" is a **group node** connected to the next slide by an **edge**. The user presses arrow keys to zoom/pan between slides along the edge chain.

**Requirements**:
- Advanced Canvas plugin installed in Obsidian (515K+ downloads, actively maintained)
- Each slide is a `group` node (zones)
- Slides are connected by edges in sequence (slide 1 → slide 2 → slide 3...)
- Slide content (text, images) is placed inside the slide's group bounds

---

## Slide Dimensions

| Style | Group Width | Group Height | Use Case |
|-------|------------|-------------|----------|
| **Deck** (16:9) | 1200 | 675 | Standard presentations |
| **Storyboard** (16:9) | 1920 | 1080 | Video planning with annotations |
| **Compact** (4:3) | 960 | 720 | Dense content, smaller screens |

**Recommended**: 1200×675 for most presentations. Obsidian auto-fits each slide group to the viewport on navigation.

---

## Slide Structure

Each slide is a group node containing child nodes:

```json
{
  "id": "zone-slide-1-1744032823",
  "type": "group",
  "label": "Slide 1: Introduction",
  "x": 0, "y": 0,
  "width": 1200, "height": 675,
  "color": "4"
}
```

### Content Inside a Slide

Place nodes spatially inside the group's bounds. Common patterns:

**Title slide**:
```
┌─────────────────────────────────┐
│  Slide 1: Title                  │
│  ┌───────────────────────────┐  │
│  │  # Presentation Title     │  │
│  │  Author • Date            │  │
│  │                           │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**Content slide** (text + image):
```
┌─────────────────────────────────┐
│  Slide 2: Key Finding           │
│  ┌──────────┐  ┌────────────┐  │
│  │ ## Title  │  │            │  │
│  │ • Point 1 │  │   image    │  │
│  │ • Point 2 │  │            │  │
│  │ • Point 3 │  │            │  │
│  └──────────┘  └────────────┘  │
└─────────────────────────────────┘
```

**Full-text slide**:
```
┌─────────────────────────────────┐
│  Slide 3: Deep Dive             │
│  ┌───────────────────────────┐  │
│  │  ## Section Title         │  │
│  │  Detailed content with    │  │
│  │  multiple paragraphs,     │  │
│  │  callouts, and lists.     │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Content Node Sizing Inside Slides

| Content Type | Width | Height | Position |
|-------------|-------|--------|----------|
| Full-width text | slide_w - 60 (1140) | varies | x+30, y+60 |
| Half-width text | slide_w/2 - 40 (560) | varies | x+20, y+60 |
| Half-width image | slide_w/2 - 40 (560) | auto | x+slide_w/2+10, y+60 |
| Caption text | slide_w - 60 (1140) | 60 | x+30, y+slide_h-80 |

---

## Slide Navigation Edges

Connect slides sequentially with edges. Advanced Canvas follows edge chains for navigation.

```json
{
  "id": "e-slide-1-2-1744032823",
  "fromNode": "zone-slide-1-1744032823",
  "toNode": "zone-slide-2-1744032823",
  "toEnd": "arrow"
}
```

**Rules**:
- Omit `fromSide`/`toSide` for auto-routing
- Use `toEnd: "arrow"` to show flow direction
- Edges must form a single linear chain (no branching for standard presentations)
- For branching presentations: create multiple edge paths from decision slides

---

## Slide Layout

### Vertical Stack (Recommended)

Stack slides top-to-bottom with consistent gaps:

```
y=0:      [Slide 1: Title]          (1200 × 675)
          │
y=775:    [Slide 2: Problem]        (1200 × 675)
          │
y=1550:   [Slide 3: Solution]       (1200 × 675)
          │
y=2325:   [Slide 4: Results]        (1200 × 675)
```

Gap between slides: 100px (y_next = y_prev + 675 + 100 = y_prev + 775).

### Horizontal Flow

For storyboard-style presentations, arrange left-to-right:

```
x=0       x=1300      x=2600
[Slide 1] → [Slide 2] → [Slide 3]
```

Gap: 100px (x_next = x_prev + 1200 + 100 = x_prev + 1300).

---

## Script Annotation Column (Optional)

For video storyboards and speaker notes, add a text column to the right of each slide:

```
┌──────────────────┐  ┌────────────┐
│  Slide 1         │  │ SCRIPT     │
│  [visual content]│  │ Speaker    │
│                  │  │ notes and  │
│                  │  │ timing     │
└──────────────────┘  └────────────┘
```

**Annotation sizing**: width=500, height=slide_height, x=slide_x+slide_w+40

This mirrors the youtube-explainer canvas pattern in claude-obsidian.

---

## Color Coding for Slides

| Slide Type | Color | Use |
|-----------|-------|-----|
| Title/Intro | `"6"` (purple) | Opening slide |
| Content | `"4"` (green) | Standard content |
| Key Finding | `"5"` (cyan) | Important data/insight |
| Warning/Risk | `"1"` (red) | Problems, risks |
| Action Item | `"2"` (orange) | Next steps, todos |
| Summary/Close | `"6"` (purple) | Closing slide |

---

## Standard Slide Deck Structure

A typical presentation follows this pattern:

1. **Title Slide** — Project name, author, date (color: 6)
2. **Agenda/Overview** — What will be covered (color: 4)
3. **Context/Problem** — Why this matters (color: 4)
4. **Content Slides** — 2-4 slides of findings/features (color: 4/5)
5. **Key Insight** — The main takeaway (color: 5)
6. **Next Steps** — Action items (color: 2)
7. **Questions/Close** — Q&A or closing (color: 6)

Target: 6-10 slides. More than 12 slides risks performance issues and attention loss.

---

## Performance Notes

- Keep total node count under 120 (slides × ~4 nodes per slide = 48 for 12 slides)
- Limit images to 1-2 per slide (large images cause lag during transitions)
- Mermaid diagrams in text nodes work well for data slides
- GIFs play during presentation but consume GPU — limit to 1 per deck
- SVG diagrams are lightweight and recommended for charts
