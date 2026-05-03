import { startNewChat } from '../app/actions/chat';

export default function Home() {
  return (
    <main className = "flex min-h-screen flex-col items-center p-8 bg-gray-50">
      <div className = "w-full max-w-3xl bg-white rounded-xl shadow-lg p-6 flex flex-col h-[85vh]">
        <h1 className = "text=2xl font-bold text-gray-800 border-b pb-4 mb-4">
          Local Meeting Summariser
        </h1>

        <p className = "text-gray-500 mb-8 leading-relaxed">
          Search through thousands of meeting transcripts instantly. Ask questions about past decisions, action items and project timelines locally and securely.
        </p>

        <form action = { startNewChat }>
          <button
            type = "submit"
            className = "bg-blue-600 text-white px-8 py-4 rounded-xl font-semibold shadow-sm hover:bg-blue-700 hover:shadow transform hover:-translate-y-0.5 transition-all duration-250"
          >
            Start a New Conversation
          </button>
        </form>
      </div>
    </main>
  );
}