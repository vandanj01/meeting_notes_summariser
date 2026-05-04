'use client';

import { useState } from 'react';
import { saveMessage, updateSessionTitle, type Source } from '../src/app/actions/chat';
import FileUpload from '../components/FileUpload';

interface Message {
    role: 'user' | 'ai';
    content: string;
    sources?: Source[];
}

interface ChatInterfaceProps {
    sessionId: string;
    initialMessages: Message[];
}

export default function ChatInterface({ sessionId, initialMessages }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleUploadComplete = (filename: string) => {
        setMessages((prev) => [...prev, 
            {
                role: "ai",
                content: `Successfully read **${filename}**`,
                sources: [],                
            },
        ]);
    };

    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if(!input.trim() || !sessionId)
            return;

        const isFirstMessage = messages.length === 0;
        
        const historyForBackend = messages.map((msg) => ({
            role: msg.role,
            content: msg.content,
        }));

        const userMessage: Message = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        await saveMessage(sessionId, 'user', userMessage.content);

        if(isFirstMessage) {
            fetch('http://localhost:8000/api/title', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMessage.content }),
            })
            .then(res => res.json())
            .then(data => {
                if(data.title) {
                    updateSessionTitle(sessionId, data.title);
                }
            })
            .catch(err => console.error("Title generation failed: ", err));
        }

        try {
            const response =await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userMessage.content,
                    chat_history: historyForBackend
                }),
            });

            const data = await response.json();

            const safeContent = data.answer || data.result || data.output || "I found the relevant documents, but the model failed to generate a text summary.";

            const aiMessage: Message = {
                role: 'ai',
                content: safeContent,
                sources: data.sources || [],
            };

            setMessages((prev) => [...prev, aiMessage]);
            await saveMessage(sessionId, 'ai', aiMessage.content, aiMessage.sources);
        }
        catch(error) {
            console.error("Chat API error: ", error);
            setMessages((prev) => [...prev, { role: 'ai', content: "Sorry, an error occurred while connecting to the backend." }]);
        }
        finally {
            setIsLoading(false);
        }
    };

    return (
        <main className = "flex min-h-screen flex-col items-center p-8 bg-gray-50">
            <div className = "w-full max-w-3xl bg-white rounded-xl shadow-lg p-6 flex flex-col h-[85vh]">
                <h1 className = "text=2xl font-bold text-gray-800 border-b pb-4 mb-4">
                    Local Meeting Summariser
                </h1>

                <div className = "flex-1 overflow-y-auto space-y-6 mb-4 pr-2">
                    { messages.length === 0 ? (
                        <p className = "text-gray-400 text-center mt-20">Ask a question about your meetings to get started.</p>
                    ) : (
                        messages.map((msg, index) => (
                            <div key = { index } className = {`flex flex-col ${ msg.role === 'user' ? 'items-end' : 'items-start' }`}>
                                <div className = {`max-w-[80%] rounded-lg p-4 ${ msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                                    <p>{ msg.content }</p>
                                </div>

                                { msg.sources && msg.sources.length > 0 && (
                                    <div className = "mt-2 flex flex-wrap gap-2 max-w-[80%]">
                                        { msg.sources.map((source, index) => (
                                            <span key = { index } className = "text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded border border-indigo-100">
                                                { source.title }
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                    { isLoading && (
                        <div className = "text-gray-400 text-sm animate-pulse">
                            The AI is thinking...
                        </div>
                    )}
                </div>

                <form onSubmit = { sendMessage } className = "flex gap-2">

                    <FileUpload onUploadComplete = { handleUploadComplete } />

                    <input 
                        type = "text" 
                        value = { input }
                        onChange = { (e) => setInput(e.target.value) }
                        placeholder = "What did we decide about the long beach project?"
                        className = "flex-1 rounded-lg border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                        disabled = { isLoading }
                    />

                    <button
                        type = "submit"
                        disabled = { isLoading || !input.trim() }
                        className = "bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
                    >
                        Send
                    </button>
                </form>
            </div>
        </main>
    );
}