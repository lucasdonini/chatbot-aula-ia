// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { MarkdownResponse } from './MarkdownResponse'

afterEach(cleanup)

describe('MarkdownResponse', () => {
  it('renderiza Markdown e rebaixa os títulos principais', () => {
    render(<MarkdownResponse content="# Resposta" />)

    expect(screen.getByRole('heading', { level: 3, name: 'Resposta' })).toBeTruthy()
  })

  it('não renderiza HTML recebido na resposta', () => {
    const { container } = render(
      <MarkdownResponse content={'Texto seguro\n\n<script>alert("xss")</script>'} />,
    )

    expect(screen.getByText('Texto seguro')).toBeTruthy()
    expect(container.querySelector('script')).toBeNull()
    expect(container.textContent).not.toContain('alert("xss")')
  })
})
