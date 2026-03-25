import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-slate-900">EDIP UI Home</h1>
        <p className="text-slate-600">Frontend is running successfully.</p>
        <Link
          href="/chat"
          className="inline-block rounded-xl bg-slate-900 px-5 py-3 text-white"
        >
          Open Chat Page
        </Link>
      </div>
    </main>
  );
}