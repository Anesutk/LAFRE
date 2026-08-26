import { redirect } from 'next/navigation';

export default function StudentHomeRedirect() {
  redirect('/chat');
}
