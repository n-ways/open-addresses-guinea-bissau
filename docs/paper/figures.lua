-- In the PDF a figure uses its vector PDF; the markdown on the web uses the SVG.
function Image(img)
  img.src = img.src:gsub('%.svg$', '.pdf')
  return img
end

-- An unnumbered chapter (availability, acknowledgements, references) sets its own running head,
-- so the head does not repeat the last numbered section.
function Header(h)
  if FORMAT:match('latex') and h.level == 1 and h.classes:includes('unnumbered') then
    local title = pandoc.utils.stringify(h.content)
    return {h, pandoc.RawBlock('latex', '\\markboth{' .. title .. '}{}')}
  end
end

-- A table of moderate length starts on a new page when the rest of the page cannot hold it,
-- so that it is not split after its first rows (longtable breaks between any two rows).
-- When the table directly follows a heading, the heading moves with it.
local function table_lines(t)
  local lines = 5
  local function count(rows)
    for _, row in ipairs(rows) do
      local longest = 0
      for _, cell in ipairs(row.cells) do
        longest = math.max(longest, #pandoc.utils.stringify(cell.contents))
      end
      lines = lines + math.max(1, math.ceil(longest / 40))
    end
  end
  count(t.head.rows)
  for _, body in ipairs(t.bodies) do count(body.body) end
  return lines
end

function Pandoc(doc)
  if not FORMAT:match('latex') then return nil end
  local out = {}
  for _, b in ipairs(doc.blocks) do
    if b.t == 'Table' then
      local lines = table_lines(b)
      if lines <= 40 then
        local at = #out + 1
        if at > 1 and out[at - 1].t == 'Header' then
          at = at - 1
          lines = lines + 4
        end
        table.insert(out, at, pandoc.RawBlock('latex', '\\needspace{' .. lines .. '\\baselineskip}'))
      end
    end
    table.insert(out, b)
  end
  doc.blocks = out
  return doc
end
