import Link from 'next/link';
import { getAllSessions, startNewChat } from '../src/app/actions/chat';
import DeleteButton from './DeleteButton';

export default async function Sidebar() {
    const sessions = await getAllSessions();

    return (
        <div className = "w-64 bg-gray-900 text-white h-screen flex flex-col">
            <div className = "p-4">
                <form action = { startNewChat }>
                    <button
                        type = "submit"
                        className = "w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex justify-center items-center gap-2"
                    >
                        <span className = "text-xl">+</span>
                        New Chat
                    </button>
                </form>
            </div>

            <div className = "flex-1 overflow-y-auto mt-2">
                <h2 className = "text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 mb-2">
                    Past Conversations
                </h2>
                <ul className = "space-y-1 px-2">
                    {sessions.map((session) => (
                        <li key = { session.id } className = "group relative flex items-center rounded-md hover:bg-gray-800 transition-colors">
                            <Link
                                href={ `/c/${ session.id }` }
                                className = "flex-1 block px-3 py-2 pr-8 text-sm text-gray-300 hover:bg-gray-800 group-hover:text-white truncate"
                            >
                                { session.title }
                            </Link>

                            <div className = "absolute right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <DeleteButton id = { session.id } />
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}