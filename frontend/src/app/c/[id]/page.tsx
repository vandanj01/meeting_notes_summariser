import { getChatHistory } from '../../actions/chat';
import ChatInterface from '../../../../components/ChatInterface';

export default async function DynamicChatPage({ params }: { params: Promise<{ id: string }> }) {
    const resolvedParams = await params;
    const history = await getChatHistory(resolvedParams.id);

    return (
        <div className = "h-full max-w-4xl mx-auto w-full pt-8 pb-8 pr-8">
            <ChatInterface sessionId = { resolvedParams.id } initialMessages = { history } />
        </div>
    );
}
