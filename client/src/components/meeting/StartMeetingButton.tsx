import { DoorOpen, Play } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { Button } from '@/components/ui/button'
import { useActiveMeeting, useStartMeeting } from '@/hooks/queries'
import { ApiError } from '@/lib/api'

/** "Join meeting" when the team is already meeting, "Start meeting" when it can be started, else nothing. */
export function StartMeetingButton({ teamId }: { teamId: string }) {
  const { canWrite } = useAuth()
  const navigate = useNavigate()
  const active = useActiveMeeting(teamId)
  const start = useStartMeeting(teamId)
  const room = (id: string) => `/teams/${teamId}/meeting/${id}`

  if (active.data) {
    return <Button onClick={() => navigate(room(active.data!.id))}><DoorOpen /> Join meeting</Button>
  }
  if (!canWrite || active.isLoading) return null
  return (
    <Button
      disabled={start.isPending}
      onClick={() =>
        start.mutate(undefined, {
          onSuccess: (m) => navigate(room(m.id)),
          // Two people pressed Start together: the loser simply joins the winner's meeting.
          onError: async (e) => {
            if (!(e instanceof ApiError && e.status === 409)) return
            const current = (await active.refetch()).data
            if (current) navigate(room(current.id))
          },
        })
      }
    >
      <Play /> Start meeting
    </Button>
  )
}
