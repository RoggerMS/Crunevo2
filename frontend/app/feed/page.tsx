'use client'
import { useEffect, useState } from 'react'

interface FeedItem {
  id: number
  title: string
}

export default function FeedPage() {
  const [items, setItems] = useState<FeedItem[]>([])

  useEffect(() => {
    fetch('/api/feed')
      .then((res) => res.json())
      .then((data) => setItems(data))
      .catch((err) => console.error(err))
  }, [])

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Feed</h1>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id} className="p-2 border rounded">
            {item.title}
          </li>
        ))}
      </ul>
    </div>
  )
}
