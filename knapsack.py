import numpy as np

class ROI:
    def __init__(self, df, ytrue, ypred, threshold=0.8, name='pipeline', seed=42):
        self.df = df.copy()
        self.df['true'] = ytrue
        self.df['pred'] = ypred
        self.df.sort_values('pred', ascending=False, inplace=True)
        self.threshold_ = threshold
        self.name_ = name
        self.seed_ = seed

    def make_LTV(self):
        self.mean_sal = self.df.EstimatedSalary.mean()
        self.df['LTV'] = round(self.df.EstimatedSalary.apply(lambda x: 0.15 * x if x < self.mean_sal else 0.2 * x), 2)

    def make_churn(self):
        self.df['churn'] = self.df.pred.apply(lambda x: 1 if x >= self.threshold_ else 0)

    def get_profit(self):
        profit = 0
        modelchurn = 0
        for i in range(self.ncards_):
            entry = self.df.iloc[i]
            if entry.true:
                profit += entry.LTV
                modelchurn += 1
        self.profit_ = profit - self.investment_
        self.modelchurn_ = 100.0 * modelchurn / self.ncards_

    def get_random(self):
        randomdf = self.df.sample(self.ncards_, random_state=self.seed_)
        profit = 0
        randomchurn = 0
        for i in range(self.ncards_):
            entry = randomdf.iloc[i]
            if entry.true:
                profit += entry.LTV
                randomchurn += 1
        self.random_profit_ = profit - self.investment_
        self.random_churn_ = 100.0 * randomchurn / self.ncards_

    def greedy_knapsack(self):
        churndf = self.df.loc[self.df.churn == 1, :].copy()
        churndf.sort_values('LTV', ascending=False, inplace=True)
        greedy = 0
        greedychurn = 0
        i = 0
        n = min(len(churndf), self.ncards_)
        while i < n:
            entry = churndf.iloc[i]
            if entry.true:
                greedy += entry.LTV
                greedychurn += 1
            i += 1
        self.used_cads_ = i
        self.greedy_profit = greedy - (n * self.gift_)
        self.greedy_churn_ = 100.0 * greedychurn / n

    def make_gift(self):
        self.incentives_ = [20000, 200, 100, 50]
        gifts = []
        n = len(self.df)
        for i in range(n):
            entry = self.df.iloc[i]
            if entry.pred >= 99:
                gifts.append(self.incentives_[0])
            elif 95 <= entry.pred < 99:
                gifts.append(self.incentives_[1])
            elif 90 <= entry.pred < 95:
                gifts.append(self.incentives_[2])
            else:
                gifts.append(self.incentives_[3])
        self.df['gift'] = gifts

    def random_gift(self):
        randomdf = self.df.sample(self.ncards_, random_state=self.seed_)
        profit = 0
        randomchurn = 0
        for i in range(self.ncards_):
            entry = randomdf.iloc[i]
            if entry.true:
                randomchurn += 1
                if entry.gift < self.incentives_[1]:
                        profit += entry.LTV
        self.realrandom_profit_ = profit - self.investment_
        self.realrandom_churn_ = 100.0 * randomchurn / self.ncards_

    def give_gift(self):
        self.make_gift()
        self.random_gift()
        givedf = self.df[self.df.churn == 1]
        W = int(self.investment_ / self.incentives_[-1])
        vals = givedf.LTV.astype(int).values
        wt = (givedf.gift / self.incentives_[-1]).astype(int).values
        max_val, keep = self.knapsack(W, wt, vals)
        self.givedf = givedf.iloc[keep]
        profit = 0
        modelchurn = 0
        n = len(self.givedf)
        for i in range(n):
            entry = self.givedf.iloc[i]
            if entry.true:
                profit += (entry.LTV - entry.gift)
                modelchurn += 1
            else:
                profit += (0 - entry.gift)
        self.real_profit = profit
        self.real_churn = 100.0 * modelchurn / n

    def knapsack(self, W, wt, vals):
        n = len(vals)
        K = np.zeros((n + 1, W + 1))
        for i in range(n + 1):
            for w in range(W + 1):
                if i == 0 or w == 0:
                    K[i][w] = 0
                elif wt[i - 1] <= w:
                    K[i][w] = max(vals[i - 1] + K[i - 1][w - wt[i - 1]], K[i - 1][w])
                else:
                    K[i][w] = K[i - 1][w]
        res = K[n][W]
        w = W
        keep = []
        for i in range(n, 0, -1):
            if res <= 0:
                break
            if res == K[i - 1][w]:
                continue
            else:
                keep.append(i - 1)
                res -= vals[i - 1]
                w -= wt[i - 1]
        return K[n][W], keep

    def get_ROI(self):
        self.make_LTV()
        self.make_churn()
        self.get_profit()
        self.get_random()
        self.greedy_knapsack()
        self.give_gift()

    def print_performance(self, investment=10000, gift=100, show=True):
        self.investment_ = investment
        self.gift_ = gift
        self.ncards_ = int(investment / gift)
        self.get_ROI()
        if show:
            print(f'Performance of {self.name_} - select the {self.ncards_} clients with highest churn probability')
            print(f'ROI = ${self.profit_:,.2f}')
            print(f'Percentage of {self.ncards_} clients that were correctly identified as churning clients: {self.modelchurn_:,.2f}%')

            print(f'\nPerformance of selecting the {self.used_cads_} richest clients (with Pchurn > {self.threshold_})')
            print(f'ROI = ${self.greedy_profit:,.2f}')
            print(f'Percentage of {self.ncards_} clients that were correctly identified as churning clients: {self.greedy_churn_:,.2f}%')

            print(f'\nPerformance of randomly selecting clients (in realistic scenario):')
            print(f'ROI = ${self.random_profit_:,.2f}')
            print(f'Percentage of {self.ncards_} clients that were correctly identified as churning clients: {self.random_churn_:,.2f}%')

            print(f'\nPerformance of model in selecting clients (in realistic scenario):')
            print(f'ROI = ${self.real_profit:,.2f}')
            print(f'Percentage of {len(self.givedf)} clients that were correctly identified as churning clients: {self.real_churn:,.2f}%')
            print(f'Total Invested: ${self.givedf.gift.sum():,}')

            print(f'\nPerformance of randomly selecting clients (in realistic scenario):')
            print(f'ROI = ${self.realrandom_profit_:,.2f}')
            print(f'Percentage of {self.ncards_} clients that were correctly identified as churning clients: {self.realrandom_churn_:,.2f}%')

    def get_results(self, investment=10000, gift=100):
        self.print_performance(investment=investment, gift=gift, show=False)
        results = {}
        results['model'] = [self.name_]
        results = pd.DataFrame.from_dict(results)
        results['threshold'] = [self.threshold_]
        return results
