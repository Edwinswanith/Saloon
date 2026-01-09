---
name: Saloon Tool Letter Typography
overview: Create custom SVG letter components where key letters (P, N, C, A, R, U, E) are designed using saloon tool shapes (scissors, combs, brushes, makeup tools) to form professional, brand-consistent letter shapes. Integrate these custom letters into the GlobalHeader banner text.
todos:
  - id: create_saloon_letters
    content: Create SaloonLetters.jsx component file with custom SVG letter components (P, N, C, A, R, U, E) using saloon tool shapes
    status: pending
  - id: design_letter_svgs
    content: Design SVG paths for each letter using saloon tools (scissors, combs, brushes) to form recognizable letter shapes
    status: pending
    dependencies:
      - create_saloon_letters
  - id: create_text_renderer
    content: Create SaloonText component that renders custom letters for key characters and falls back to regular text for others
    status: pending
    dependencies:
      - design_letter_svgs
  - id: update_global_header
    content: Update GlobalHeader.jsx to import and use SaloonText component instead of plain text
    status: pending
    dependencies:
      - create_text_renderer
  - id: update_css_styling
    content: Update GlobalHeader.css to style custom letter components and ensure responsive design
    status: pending
    dependencies:
      - update_global_header
---

# Saloon Tool Letter Typography Implementation

## Goal

Design custom SVG letter components where key letters in "Priyanka Nature Cure" are shaped using saloon tools (scissors, combs, brushes, makeup tools) to create a unique, professional brand identity.

## Approach

Create custom SVG letter components that use saloon tool shapes to form letter outlines. Focus on key letters: **P** (Priyanka), **N** (Nature), **C** (Cure), plus **A**, **R**, **U**, **E** for visual consistency.

## Design Concept

Each letter will be constructed using saloon tool elements:

- **P**: Scissors forming the vertical line, comb teeth forming the curve
- **N**: Two brushes forming the vertical lines, a comb forming the diagonal
- **C**: Curved brush or comb forming the C shape
- **A**: Scissors forming the sides, comb forming the crossbar
- **R**: Similar to P but with a brush forming the leg
- **U**: Two brushes/curved tools forming the U shape
- **E**: Brushes forming vertical lines, comb forming horizontal lines

## Implementation Steps

### 1. Create Custom Letter Component File

Create `frontend/src/components/SaloonLetters.jsx`:

- Export individual letter components (SaloonP, SaloonN, SaloonC, SaloonA, SaloonR, SaloonU, SaloonE)
- Each component accepts props: `size`, `color`, `className`
- Use inline SVG with saloon tool shapes forming letter outlines
- Ensure letters are readable and maintain brand color (#0F766E)

### 2. Design SVG Letter Shapes

For each letter, create SVG paths using saloon tool elements:

- Use `path` elements to draw tool shapes (scissors, combs, brushes)
- Position tools to form recognizable letter shapes
- Maintain consistent stroke width and styling
- Use brand colors with subtle variations

### 3. Create Text Renderer Component

Create `SaloonText` component in `SaloonLetters.jsx`:

- Accepts text string and renders custom letters where available
- Falls back to regular text for non-customized letters
- Maintains proper spacing and alignment
- Handles responsive sizing

### 4. Update GlobalHeader Component

Modify `frontend/src/components/GlobalHeader.jsx`:

- Import `SaloonText` component
- Replace current text rendering with `SaloonText` component
- Pass "Priyanka Nature Cure" as text prop
- Maintain existing CSS classes for styling

### 5. Update CSS Styling

Update `frontend/src/components/GlobalHeader.css`:

- Style custom letter components to match existing banner design
- Ensure proper sizing and spacing
- Maintain responsive breakpoints
- Keep decorative elements (lines with dots) intact

## Files to Create/Modify

1. **Create**: `frontend/src/components/SaloonLetters.jsx`

- Custom SVG letter components
- SaloonText renderer component

2. **Modify**: `frontend/src/components/GlobalHeader.jsx`

- Import and use SaloonText component
- Replace current text rendering

3. **Modify**: `frontend/src/components/GlobalHeader.css`

- Add styles for custom letter components
- Ensure responsive design

## Technical Details

### SVG Design Principles

- Use `viewBox` for scalable SVGs
- Maintain aspect ratios for readability
- Use `stroke` and `fill` for tool shapes
- Ensure minimum stroke width of 2px for visibility
- Use `transform` for positioning tool elements

### Letter-to-Tool Mapping

- **P**: Scissors (vertical) + Comb (curve)
- **N**: Brushes (verticals) + Comb (diagonal)
- **C**: Curved brush/comb
- **A**: Scissors (sides) + Comb (crossbar)
- **R**: Scissors (vertical) + Comb (curve) + Brush (leg)
- **U**: Curved brushes/tools
- **E**: Brushes (vertical) + Combs (horizontal)

### Responsive Considerations

- Scale SVG viewBox proportionally
- Maintain letter spacing at all sizes
- Ensure readability on mobile (minimum 16px height)
- Use CSS `max-width` and `height: auto` for SVGs

## Testing Checklist

- [ ] Custom letters render correctly in desktop view
- [ ] Letters are readable and recognizable
- [ ] Responsive design works on tablet (768px)
- [ ] Responsive design works on mobile (480px)
- [ ] Brand colors are consistent (#0F766E variations)
- [ ] Letter spacing is appropriate
- [ ] Fallback text renders for non-customized letters
- [ ] No console errors or warnings
- [ ] SVG scaling works correctly
- [ ] Performance is acceptable (no lag)

## Design Notes

- Letters should be elegant and professional
- Tool shapes should be subtle enough to read as letters
- Maintain brand consistency with existing design
- Ensure accessibility (letters must be readable)
- Consider adding `aria-label` for screen readers