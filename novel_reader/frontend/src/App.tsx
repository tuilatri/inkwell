import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import Library from './pages/Library'
import Login from './pages/Login'
import Reader from './pages/Reader'

export default function App() {
  return (
    <TooltipProvider delayDuration={200}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Library />} />
          <Route path="/read/:chapterId" element={<Reader />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  )
}
