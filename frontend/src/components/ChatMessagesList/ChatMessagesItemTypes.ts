import { type QuestionMessage } from '../../types/messageTypes'
import { State } from '../../widgets/VideoAssistant/hooks/useChatTypes'

export interface ChatMessagesItemProps {
    message: QuestionMessage
    index: number
    handleShow: (index: number | undefined, indexOfElementInArray: number) => void
    key: number
}