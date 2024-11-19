import { AudioProcessor } from '../components/AudioProcessor';
import { ProcessingHistory } from '../components/ProcessingHistory';

const Home = () => {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Audio Source Separation</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <AudioProcessor />
        </div>
        <div>
          <ProcessingHistory />
        </div>
      </div>
    </div>
  );
};

export default Home;
