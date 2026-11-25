import { chromium, expect, test, type Browser, type BrowserContext, type Locator, type Page } from '@playwright/test'
import { cursorOverlay } from './cursor-overlay'

/**
 * Two browsers, one meeting: the facilitator advances the agenda and the second browser follows on its own.
 *
 * Fixture and clock: the stack is started from the seeded database with the server clock pinned (APP_NOW in
 * docker-compose.yml), so both browsers see the same business time and the same data. The test never touches the
 * clock. It ends the meeting it started, and ends a meeting left over from an aborted run first, so it can be
 * re-run against the same stack.
 */

const TEAM = 'team_lead'
const FACILITATOR = 'blake@acme.test' // seeded Team Member, member of team_lead
const ATTENDEE = 'casey@acme.test' // seeded Team Member, member of team_lead

// Headed runs (HEADED=1) pause after each step so a person can watch; STEP_DELAY_MS changes how long. Headless: none.
const STEP_DELAY_MS = process.env.HEADED ? Number(process.env.STEP_DELAY_MS ?? 2000) : 0
const pause = (page: Page) => (STEP_DELAY_MS ? page.waitForTimeout(STEP_DELAY_MS) : Promise.resolve())

// Playwright moves the mouse to a target in one jump. Headed runs glide it there in small steps first, then click.
async function press(target: Locator): Promise<void> {
  if (process.env.HEADED) {
    await target.scrollIntoViewIfNeeded()
    const box = await target.boundingBox()
    if (box) await target.page().mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 40 })
  }
  await target.click()
}

// Headed runs put the two windows side by side: Blake on the left half of the screen, Casey on the right.
// Chromium takes its window position as a launch argument, so each person gets their own browser instance then.
// SCREEN_WIDTH / SCREEN_HEIGHT describe the display (default 1440x900).
const SCREEN_WIDTH = Number(process.env.SCREEN_WIDTH ?? 1440)
const SCREEN_HEIGHT = Number(process.env.SCREEN_HEIGHT ?? 900)
const opened: Browser[] = []

async function newContext(browser: Browser, baseURL: string | undefined, side: 'left' | 'right'): Promise<BrowserContext> {
  if (!process.env.HEADED) return browser.newContext() // headless: the config's browser, so its trace covers this
  const half = Math.floor(SCREEN_WIDTH / 2)
  const own = await chromium.launch({
    headless: false,
    args: [`--window-position=${side === 'left' ? 0 : half},0`, `--window-size=${half},${SCREEN_HEIGHT}`],
  })
  opened.push(own)
  return own.newContext({ baseURL, ignoreHTTPSErrors: true, viewport: null }) // viewport null: the page fills the window
}

test.afterEach(async () => {
  await Promise.all(opened.splice(0).map((b) => b.close()))
})

async function signedInPage(browser: Browser, baseURL: string | undefined, email: string, side: 'left' | 'right'): Promise<Page> {
  const context = await newContext(browser, baseURL, side) // its own storage: a different person in a different browser
  if (process.env.HEADED) await context.addInitScript(cursorOverlay) // visible cursor and click ripple for watchers
  const page = await context.newPage()
  await page.goto('/')
  await page.getByLabel('Email').fill(email)
  await press(page.getByRole('button', { name: 'Sign in' }))
  await expect(page.getByLabel('Email')).toHaveCount(0) // the sign-in form is gone: we are in
  return page
}

test.beforeAll(async ({ request }) => {
  // A meeting left running by an aborted run would turn "Start meeting" into "Join meeting". Only a meeting's own
  // facilitator can end it, and a run that was aborted was always started by FACILITATOR, so end it as them.
  const login = await request.post('/api/auth/login', { data: { email: FACILITATOR } })
  const headers = { Authorization: `Bearer ${(await login.json()).access_token}` }
  const active = await (await request.get(`/api/teams/${TEAM}/meetings/active`, { headers })).json()
  if (active) {
    const ended = await request.post(`/api/meetings/${active.id}/end`, { headers })
    expect(ended.ok(), 'a meeting not started by this test is running; reset the stack').toBeTruthy()
  }
})

test('the second browser follows when the facilitator advances the agenda', async ({ browser, baseURL }) => {
  const section = (page: Page) => page.getByTestId('current-section')

  // Blake signs in and starts the meeting from the team page. He lands in the room, on the first agenda section.
  const facilitator = await signedInPage(browser, baseURL, FACILITATOR, 'left')
  await facilitator.goto(`/teams/${TEAM}`)
  await press(facilitator.getByRole('button', { name: 'Start meeting' }))
  await expect(facilitator).toHaveURL(/\/meeting\/.+/)
  await expect(section(facilitator)).toHaveText('Scorecard')
  await pause(facilitator)

  // Only now does Casey sign in. A meeting is already running, so their team page offers "Join", not "Start".
  const attendee = await signedInPage(browser, baseURL, ATTENDEE, 'right')
  await attendee.goto(`/teams/${TEAM}`)
  await expect(attendee.getByRole('button', { name: 'Start meeting' })).toHaveCount(0)
  await expect(attendee.getByRole('button', { name: 'Join meeting' })).toBeVisible()
  await pause(attendee)
  await press(attendee.getByRole('button', { name: 'Join meeting' }))
  await expect(attendee).toHaveURL(/\/meeting\/.+/)
  await expect(section(attendee)).toHaveText('Scorecard')
  await expect(attendee.getByRole('button', { name: 'Next section' })).toHaveCount(0) // only the facilitator advances
  await pause(attendee)

  // Both see each other as attendees (live presence).
  await expect(facilitator.getByText('Attendees (2)')).toBeVisible()
  await expect(attendee.getByText('Attendees (2)')).toBeVisible()
  await pause(attendee)

  // Blake advances. Casey's page changes by itself: no reload, no click.
  await press(facilitator.getByRole('button', { name: 'Next section' }))
  await expect(section(facilitator)).toHaveText('IDS')
  await expect(section(attendee)).toHaveText('IDS')
  await pause(attendee)

  // Clean up so the test can run again: the facilitator ends the meeting and the attendee sees it end.
  facilitator.once('dialog', async (dialog) => {
    await pause(facilitator) // headed: leave the "End the meeting for everyone?" prompt on screen for a moment
    await dialog.accept()
  })
  await press(facilitator.getByRole('button', { name: 'End meeting' }))
  await expect(section(attendee)).toHaveText('Ended')
  await pause(attendee)
})
