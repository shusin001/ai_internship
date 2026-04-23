import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

export default function MainLayout() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="app-shell p-8">
        <Outlet />
      </main>
    </div>
  );
}
