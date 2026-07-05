/**
 * TechMart AI Support — Main Page (Next.js)
 * This is the entry point for the Next.js frontend.
 * The full chat UI is in components/ChatApp.jsx
 */
import Head from "next/head";
import dynamic from "next/dynamic";

// Dynamically import to avoid SSR issues with browser APIs
const ChatApp = dynamic(() => import("../components/ChatApp"), { ssr: false });

export default function Home() {
  return (
    <>
      <Head>
        <title>TechMart AI Support</title>
        <meta name="description" content="Multi-Agent AI Customer Support for TechMart Electronics" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <ChatApp />
    </>
  );
}
