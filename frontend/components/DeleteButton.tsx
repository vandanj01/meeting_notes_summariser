'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { deleteChatSession } from '../src/app/actions/chat';

export default function DeleteButton( { id }: { id: string }) {
    const pathname = usePathname();
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDelete = async (e: React.MouseEvent) => {
        e.preventDefault();

        if(confirm('Are you sure you want to delete this conversation?')) {
            setIsDeleting(true);
            await deleteChatSession(id, pathname);
        }
    };

    return (
        <button
            onClick = { handleDelete }
            disabled = { isDeleting }
            className = "text-gray-500 hover:text-red-400 p-1 rounded-md transition-colors items-center justify-center"
            title = "Delete Chat"
        >
            { isDeleting ? 'Deleting...' : 'X' }
        </button>
    );
}