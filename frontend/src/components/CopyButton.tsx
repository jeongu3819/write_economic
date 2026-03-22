import { useState } from 'react'

interface CopyButtonProps {
  text: string
  label?: string
  showMobileCopy?: boolean
}

export default function CopyButton({ text, label = '복사', showMobileCopy = false }: CopyButtonProps): React.JSX.Element {
  const [copied, setCopied] = useState(false)
  const [mobileCopied, setMobileCopied] = useState(false)

  const wrapText = (text: string, maxLength: number = 28): string => {
    const words = text.split(' ')
    let lines = []
    let currentLine = ''

    for (const word of words) {
      if (!currentLine) {
        currentLine = word
      } else if (currentLine.length + 1 + word.length <= maxLength) {
        currentLine += ' ' + word
      } else {
        lines.push(currentLine)
        currentLine = word
      }
    }
    if (currentLine) lines.push(currentLine)
    return lines.join('\n')
  }

  const formatTextForNaver = (raw: string, isMobile: boolean) => {
    let lines = raw.split('\n')
    lines = lines.map(line => {
       let parsed = line.replace(/([가-힣a-zA-Z])\.\s+(?=[가-힣a-zA-Z])/g, '$1.\n')
       if (isMobile) {
           parsed = parsed.split('\n').map(t => wrapText(t, 28)).join('\n')
       }
       return parsed
    })
    
    return lines.join('\n')
      .replace(/^#{1,3}\s+(.*)$/gm, '$1')
      .replace(/\*\*(.*?)\*\*/g, '$1')
  }

  const formatHtmlForNaver = (raw: string, isMobile: boolean) => {
    let lines = raw.split('\n')
    let htmlLines = lines.map(line => {
       const cleanLine = line.trimEnd()
       if (!cleanLine.trim()) return ''
       
       let parsed = cleanLine
       parsed = parsed.replace(/([가-힣a-zA-Z])\.\s+(?=[가-힣a-zA-Z])/g, '$1.\n')
       parsed = parsed.replace(/\*\*(.*?)\*\*/g, '$1')
       
       const isHash = /^#{1,3}\s+/.test(parsed)
       const isNumber = /^\d+\.\s+/.test(parsed)
       const cleanedText = parsed.replace(/^#{1,3}\s+/, '')
       
       const isQuestionTitle = cleanedText.endsWith('?') && cleanedText.length < 50
       const isShortTitle = !cleanedText.endsWith('.') && !cleanedText.endsWith('다') && !cleanedText.endsWith('요') && cleanedText.length > 1 && cleanedText.length < 40 && !cleanedText.includes(' ')

       // 모바일용 자동 줄바꿈 적용
       let finalLines = parsed.split('\n')
       if (isMobile && !isHash && !isNumber && !isQuestionTitle && !isShortTitle) {
           finalLines = finalLines.map(t => wrapText(t, 28))
       }
       parsed = finalLines.join('<br/>').replace(/\n/g, '<br/>')

       if (isHash || isNumber || isQuestionTitle || (isShortTitle && !parsed.includes('<br/>'))) {
           return `<span style="font-weight:bold; background-color:#ffd1a4;">${cleanedText.replace(/\n/g, '')}</span>`
       }
       
       return parsed
    })
    
    return `<div>${htmlLines.join('<br/><br/>').replace(/(<br\/>)+/g, '<br/>')}</div>`
  }

  const handleCopy = async (e: React.MouseEvent, isMobile: boolean): Promise<void> => {
    e.stopPropagation()
    try {
      const plain = formatTextForNaver(text, isMobile)
      const html = formatHtmlForNaver(text, isMobile)

      let clipboardApiWorked = false
      if (navigator.clipboard && window.ClipboardItem) {
        try {
          const data = [
            new ClipboardItem({
              "text/plain": new Blob([plain], { type: "text/plain" }),
              "text/html": new Blob([html], { type: "text/html" })
            })
          ]
          await navigator.clipboard.write(data)
          clipboardApiWorked = true
        } catch (err) {
          console.warn('Clipboard API write failed, falling back to execCommand.', err)
        }
      }

      if (!clipboardApiWorked) {
        const tempDiv = document.createElement('div')
        tempDiv.innerHTML = html
        tempDiv.style.position = 'fixed'
        tempDiv.style.left = '-9999px'
        tempDiv.style.top = '0'
        document.body.appendChild(tempDiv)
        
        const selection = window.getSelection()
        const range = document.createRange()
        range.selectNodeContents(tempDiv)
        selection?.removeAllRanges()
        selection?.addRange(range)
        
        const success = document.execCommand('copy')
        document.body.removeChild(tempDiv)
        selection?.removeAllRanges()

        if (!success) throw new Error("execCommand failed")
      }
      
      if (isMobile) {
        setMobileCopied(true)
        setTimeout(() => setMobileCopied(false), 2000)
      } else {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    } catch(err) {
      console.error('Final copy fallback', err)
      try {
        await navigator.clipboard.writeText(formatTextForNaver(text, isMobile))
        if (isMobile) {
          setMobileCopied(true)
          setTimeout(() => setMobileCopied(false), 2000)
        } else {
          setCopied(true)
          setTimeout(() => setCopied(false), 2000)
        }
      } catch (ex) {
        console.error('All copy methods failed', ex)
      }
    }
  }

  return (
    <div style={{ display: 'inline-flex', gap: '8px' }}>
      <button className="btn btn-copy" onClick={(e) => handleCopy(e, false)}>
        {copied ? '✅ 복사 완료!' : `📋 ${label}`}
      </button>
      {showMobileCopy && (
        <button className="btn btn-copy" style={{ backgroundColor: '#2b2b2b', color: '#fff' }} onClick={(e) => handleCopy(e, true)}>
          {mobileCopied ? '✅ 모바일 복사 완료!' : `📱 모바일 복사`}
        </button>
      )}
    </div>
  )
}
