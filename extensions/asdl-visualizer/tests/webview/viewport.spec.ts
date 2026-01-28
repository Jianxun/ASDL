import { expect, test, type Page } from '@playwright/test'

test('viewport does not reset after drag', async ({ page }) => {
  await page.goto('/?dev=1')
  await page.waitForSelector('.react-flow__viewport')

  const canvas = page.locator('.reactflow')
  const canvasBox = await canvas.boundingBox()
  expect(canvasBox).not.toBeNull()
  if (!canvasBox) {
    return
  }

  await page.mouse.move(canvasBox.x + canvasBox.width / 2, canvasBox.y + canvasBox.height / 2)
  await page.mouse.wheel(0, -800)

  const scaleAfterZoom = await getViewportScale(page)
  expect(scaleAfterZoom).toBeGreaterThan(1.05)

  const node = page.locator('.instance-node').first()
  const nodeBox = await node.boundingBox()
  expect(nodeBox).not.toBeNull()
  if (!nodeBox) {
    return
  }

  await page.mouse.move(nodeBox.x + nodeBox.width / 2, nodeBox.y + nodeBox.height / 2)
  await page.mouse.down()
  await page.mouse.move(
    nodeBox.x + nodeBox.width / 2 + 120,
    nodeBox.y + nodeBox.height / 2 + 40
  )
  await page.mouse.up()

  await page.waitForTimeout(200)

  const scaleAfterDrag = await getViewportScale(page)
  expect(scaleAfterDrag).toBeGreaterThan(1.05)
  expect(Math.abs(scaleAfterDrag - scaleAfterZoom)).toBeLessThan(0.05)
})

async function getViewportScale(page: Page) {
  const transform = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport') as HTMLElement | null
    return el?.style.transform ?? ''
  })
  const match = /scale\(([^)]+)\)/.exec(transform)
  if (!match) {
    throw new Error(`Missing scale() in transform: "${transform}"`)
  }
  const scale = Number.parseFloat(match[1])
  if (!Number.isFinite(scale)) {
    throw new Error(`Invalid scale value from transform: "${transform}"`)
  }
  return scale
}
