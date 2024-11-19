import { useQuery } from '@tanstack/react-query';
import { fetchAPI } from '../api';

const Home = () => {
  const { data, isLoading, error } = useQuery({ queryKey: ['entries'], queryFn: () => fetchAPI('/entries/') });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading entries</div>;

  return (
    <div>
      {data.map((entry: any) => (
        <div key={entry.id}>
          <h2>{entry.title}</h2>
          {/* Display entry details */}
        </div>
      ))}
    </div>
  );
};

export default Home;
