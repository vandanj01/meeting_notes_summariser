'use client';

import { useState } from 'react';

interface FileUploadProps {
    onUploadComplete?: (filename: string) => void;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
    const [isUploading, setIsUploading] = useState(false);
    const [message, setMessage] = useState("");

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if(!file) return;

        setIsUploading(true);
        setMessage("Uploading and Processing...");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if(response.ok && onUploadComplete) {
                setMessage(data.message);
                onUploadComplete(file.name);
            }
            else {
                setMessage("Upload failed.");
            }
        }
        catch(error) {
            setMessage("Server error, make sure FastAPI is running.");
        }
        finally {
            setIsUploading(false);
            event.target.value = '';
        }
    };

    return (
        <div className="relative flex items-center justify-center">
            <label 
                className={`cursor-pointer p-2 rounded-full hover:bg-gray-100 transition-colors ${
                    isUploading ? "opacity-50 cursor-not-allowed" : ""
                }`}
                title="Upload Transcript"
            >
                <input 
                    type="file" 
                    accept=".txt" 
                    onChange={ handleFileChange }
                    disabled={ isUploading }
                    className="hidden"
                />
        
                {isUploading ? (
                    <span className="text-sm font-medium text-blue-600 animate-pulse">...</span>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-gray-500">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" />
                    </svg>
                )}
            </label>
        </div>
    );
}