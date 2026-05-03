import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  return (
    <main className="flex h-full min-h-0 w-full min-w-0 justify-center overflow-hidden">
      <div className="flex h-full w-full max-w-[800px] min-w-0 flex-col px-4 sm:px-8">
        <ChatPanel />
      </div>
    </main>
  );
}
