import { Alert } from '@/components/ui/alert'

export function ErrorState({ message }: { message: string }) {
  return <Alert variant="destructive">Không thể tải dữ liệu: {message}</Alert>
}
