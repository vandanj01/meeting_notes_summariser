'use server';

import prisma from '../../../lib/prisma';
import type { Message } from '@prisma/client';
import { redirect } from 'next/navigation';
import { revalidatePath } from 'next/cache';

export async function createChatSession() {
    const session = await prisma.chatSession.create({
        data: { title: "Meeting Summary" }
    });
    return session.id;
}

export interface Source {
    date: string | null;
    meeting_uid: string | null;
    summary: string | null;
}

export async function saveMessage(sessionId: string, role: string, content: string, sources: Source[] | null = null) {
    await prisma.message.create({
        data: {
            sessionId,
            role,
            content,
            sources: sources ? JSON.stringify(sources) : null,
        }
    });
}

export async function getChatHistory(sessionId: string) {
    const messages = await prisma.message.findMany({
        where: { sessionId },
        orderBy: { createdAt: 'asc' } 
    });

    return messages.map((msg: Message) => ({
        role: msg.role as 'user' | 'ai',
        content: msg.content,
        sources: msg.sources ? JSON.parse(msg.sources) : undefined
    }));
}

export async function getAllSessions() {
    return await prisma.chatSession.findMany({
        orderBy: { updatedAt: 'desc' }
    });
}

export async function startNewChat() {
    const session = await prisma.chatSession.create({
        data: { title: "New Conversation" }
    });
    redirect(`/c/${session.id}`);
}

export async function updateSessionTitle(sessionId: string, title: string) {
    try {
        await prisma.chatSession.update(({
            where: { id: sessionId },
            data: { title: title },
        }));
    }
    catch (error) {
        console.error("Failed to update session title. ", error);
    }
}

export async function deleteChatSession(sessionId: string, currentPath: string) {
    try {
        await prisma.chatSession.delete({
            where: { id: sessionId }
        });
    }
    catch(error) {
        console.error("Failed to delete session. ", error);
        return;
    }

    revalidatePath('/', 'layout');

    if(currentPath === `/c/${sessionId}`) {
        redirect('/');
    }
}