from agents.dqn_agent import *
from abc_rl.experience_replay import *
from abc_rl.exploration import *
from utils.hyperparameters import *


class DQNPlayGround:
    def __init__(self, agent: DQNAgent, env: AtariEnv, cfg: Hyperparameters, logger: Logger):
        self.agent = agent
        self.env = env
        self.cfg = cfg
        self.logger = logger

    def train(self):
        # training
        epoch_i = 0
        training_steps = 0
        lives_counter = 1
        while training_steps < self.cfg['training_steps']:
            state, info = self.env.reset()
            if 'lives' in info.keys():
                lives_counter = info['lives']
            done = truncated = run_test = False
            step_i = reward_cumulated = 0
            # perception mapping
            obs = self.agent.perception_mapping(state, step_i)
            while (not done) and (not truncated):
                # no op for the first few steps and then select action by epsilon greedy or other exploration methods
                if len(self.agent.memory) > self.cfg['replay_start_size'] and step_i >= self.cfg['no_op']:
                    action = self.agent.select_action(obs)
                else:
                    action = self.agent.select_action(obs, RandomAction())
                # environment step
                next_state, reward_raw, done, truncated, inf = self.env.step(action)
                # reward shaping
                reward = self.agent.reward_shaping(reward_raw)
                # perception mapping next state
                next_obs = self.agent.perception_mapping(next_state, step_i)
                # store the transition

                self.agent.store(obs, action, reward, next_obs, done, truncated)
                # train the agent 1 step
                self.agent.train_one_step()
                # update the state
                obs = next_obs
                # update the reward cumulated in the episode
                reward_cumulated += reward_raw
                # debug
                if (len(self.agent.memory) > self.cfg['replay_start_size'] and
                        training_steps % self.cfg['batch_num_per_epoch'] == 0):
                    # test the agent when the training steps reach the batch_num_per_epoch
                    run_test = True
                    epoch_i += 1
                # update the training step counter of the entire training process
                training_steps += 1
                # update the step counter of the current episode
                step_i += 1

            # log the training reward
            self.logger.tb_scalar('training reward', reward_cumulated, training_steps)
            if run_test:
                # test the agent
                self.logger.msg(f'{epoch_i} test start:')
                avg_reward, avg_steps = self.test(self.cfg['agent_test_episodes'])
                # log the test reward
                self.logger.tb_scalar('avg_reward', avg_reward, epoch_i)
                self.logger.msg(f'{epoch_i} avg_reward: ' + str(avg_reward))
                # log the test steps
                self.logger.tb_scalar('avg_steps', avg_steps, epoch_i)
                self.logger.msg(f'{epoch_i} avg_steps: ' + str(avg_steps))
                # log the epsilon
                self.logger.tb_scalar('epsilon', self.agent.exploration_method.epsilon, epoch_i)
                self.logger.msg(f'{epoch_i} epsilon: ' + str(self.agent.exploration_method.epsilon))

    def test(self, test_episode_num: int):
        """
        Test the DQN agent for a given number of episodes.
        :param test_episode_num: The number of episodes for testing
        :return: The average reward and average steps per episode
        """
        env = AtariEnv(self.cfg['env_name'], frame_skip=self.cfg['skip_k_frame'], screen_size=self.cfg['screen_size'],
                       remove_flickering=False)
        exploration_method = EpsilonGreedy(self.cfg['epsilon_for_test'])
        reward_cum = 0
        step_cum = 0
        lives_counter = 1
        for i in range(test_episode_num):
            state, info = env.reset()
            if 'lives' in info.keys():
                lives_counter = info['lives']
            done = truncated = False
            step_i = 0
            while (not done) and (not truncated):
                obs = self.agent.perception_mapping(state, step_i)
                action = self.agent.select_action(obs, exploration_method)
                next_state, reward, done, truncated, inf = env.step(action)
                reward_cum += reward
                state = next_state
                step_i += 1
            step_cum += step_i
        return (reward_cum / self.cfg['agent_test_episodes'] * lives_counter,
                step_cum / self.cfg['agent_test_episodes'] * lives_counter)
