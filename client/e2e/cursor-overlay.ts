/**
 * Headed runs only: Playwright drives the page with synthetic input, so no real cursor is drawn. This script,
 * injected into every page, draws one (a dot that follows the mouse) and a ripple on each click, so a person
 * watching can see what the test is doing. It is added to the page, never to the app.
 */
export const cursorOverlay = () => {
  const install = () => {
    if (document.getElementById('pw-cursor')) return
    const style = document.createElement('style')
    style.textContent = `
      #pw-cursor { position: fixed; z-index: 2147483647; left: 0; top: 0; width: 18px; height: 18px; margin: -9px 0 0 -9px;
        border-radius: 50%; background: rgba(239, 68, 68, .85); border: 2px solid #fff; box-shadow: 0 0 6px rgba(0,0,0,.5);
        pointer-events: none; transition: transform .08s linear; }
      #pw-cursor.down { transform: scale(.7); background: rgba(220, 38, 38, 1); }
      .pw-ripple { position: fixed; z-index: 2147483646; width: 14px; height: 14px; margin: -7px 0 0 -7px; border-radius: 50%;
        border: 3px solid rgba(239, 68, 68, .9); pointer-events: none; animation: pw-ripple .6s ease-out forwards; }
      @keyframes pw-ripple { to { transform: scale(5); opacity: 0; } }`
    document.documentElement.append(style)
    const dot = document.createElement('div')
    dot.id = 'pw-cursor'
    document.documentElement.append(dot)
    const move = (e: MouseEvent) => { dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px' }
    addEventListener('mousemove', move, true)
    addEventListener('mousedown', (e) => {
      move(e)
      dot.classList.add('down')
      const ripple = document.createElement('div')
      ripple.className = 'pw-ripple'
      ripple.style.left = e.clientX + 'px'
      ripple.style.top = e.clientY + 'px'
      document.documentElement.append(ripple)
      setTimeout(() => ripple.remove(), 700)
    }, true)
    addEventListener('mouseup', () => dot.classList.remove('down'), true)
  }
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', install)
  else install()
}
